# !/usr/bin/env python
# 模拟运行环境，方便函数函数进行本地测试
import logging
import os
import threading
import time
import yaml

from kafka import KafkaProducer
import redis
from prometheus_client import PrometheusForFission

GLOBAL_FUNC_CONFIG_PATH = "../fake-fission-secret-configmap.yaml"
LOCAL_FUNC_CONFIG_PATH = "../func-config.yaml"
MAKEFILE_PATH = "../Makefile"

PATH_CONFIGS = "/configs"
PATH_SECRETS = "/secrets"
PUSHGATEWAY_URL_DEFAULT = "fh-prometheus-pushgateway.fission:9091"  # may be overwritten by configs

GLOBAL_CONFIG_KEY = "global"
LOCAL_CONFIG_KEY = "local"


def synchronized(func):
    """
    a simple function lock
    """
    func.__lock__ = threading.Lock()

    def lock_func(*args, **kwargs):
        with func.__lock__:
            return func(*args, **kwargs)

    return lock_func


class Info(object):
    """
    for Cache class
    """

    def __init__(self, value, timeout):
        """
        存储的内容和过期的时间
        :param value:
        :param timeout:
        """
        self.value = value
        self.timeout = timeout


class Cache(object):
    """cache"""

    def __init__(self):
        self.content = dict()  # key: Info

    @synchronized
    def put(self, key, func=lambda x: x, param=None, timeout=0, use_old=False, old_timeout=30):
        """
        存放信息
        :param key: 键
        :param func: 获取值的函数
        :param param: func的参数
        :param timeout: 过期时间，单位秒，0表示永不过期
        :param use_old: 当数据超时且获取新值的函数没有成功，是否返回超时了的旧数据
        :param old_timeout: 超时的数据可以继续存活的时间
        :return:
        """
        now = time.time()
        timeout += now if timeout != 0 else 0
        old_timeout += now
        value = self.get(key, no_delete=use_old)
        if value is not None:
            return value
        value = func(param)
        if value is None and use_old:
            if key in self.content:
                info = self.content[key]
                if info.timeout != 0:
                    info.timeout = old_timeout
                return info.value
        else:
            self.content[key] = Info(value, timeout)
        return value

    @synchronized
    def pop(self, key):
        if key in self.content:
            self.content.pop(key)

    def get(self, key, no_delete=False):
        """
        读取信息
        :param key: 键
        :param no_delete: 不执行删除操作
        """
        if key not in self.content:
            return None
        info = self.content[key]
        if info.timeout > time.time() or info.timeout == 0:
            return info.value
        else:
            if no_delete is False:
                self.pop(key)
            return None

    def get_and_write(self, key: str, func=lambda x: x, param=None, timeout=0, use_old=True, old_timeout=30):
        ans = self.get(key, no_delete=True)
        if ans is not None:
            return ans
        return self.put(key, func, param, timeout, use_old, old_timeout)


def add_params(con, path, key, value):
    """
    在字典中添加内容，path 是字典的路径，key是key
    """
    pos = con
    for p in path:
        if p not in pos:
            pos[p] = {}
        pos = pos[p]
    pos[key] = value


def read_config(base_dir, fns, fn):
    """读取目录下的配置文件"""
    configs = dict()
    kind = {PATH_SECRETS: "Secret", PATH_CONFIGS: "ConfigMap"}.get(base_dir, None)
    if os.path.exists(LOCAL_FUNC_CONFIG_PATH) and kind is not None:
        docs = yaml.full_load_all(open(LOCAL_FUNC_CONFIG_PATH))
        for doc in docs:
            if doc.get("kind", None) == kind:
                paths = [doc.get("metadata", {}).get("namespace", "none"), doc.get("metadata", {}).get("name", "none")]
                for k, v in doc.get("data", {}).items():
                    add_params(configs, paths, k, v)
    if os.path.exists(GLOBAL_FUNC_CONFIG_PATH) and kind is not None:
        docs = yaml.full_load_all(open(GLOBAL_FUNC_CONFIG_PATH))
        for doc in docs:
            if doc.get("kind", None) == kind:
                paths = [doc.get("metadata", {}).get("namespace", "none"), doc.get("metadata", {}).get("name", "none")]
                for k, v in doc.get("data", {}).items():
                    add_params(configs, paths, k, v)
    # set alias, make it easy for user to get the parameters
    if "fission-secret-configmap" in configs:
        configs[GLOBAL_CONFIG_KEY] = configs["fission-secret-configmap"].get("fission-function-global-configmap", {})
    local_key = "func-{}".format(fn)
    if fns in configs and local_key in configs.get(fns, {}):
        configs[LOCAL_CONFIG_KEY] = configs.get(fns, {}).get(local_key, {})
    return configs


def read_func_info():
    info = dict()
    for line in open(MAKEFILE_PATH):
        if "split-line" in line:
            break
        if len(line) != 0 and line[0] != '#':
            words = line.split("=")
            if len(words) == 2:
                if "project_name" == words[0].strip():
                    info["pn"] = words[1].strip()
                elif "module_name" == words[0].strip():
                    info["mn"] = words[1].strip()
                elif "func_name" == words[0].strip():
                    info["fn"] = words[1].strip()
    return info


class FissionBaseEnvironment:
    def __init__(self):
        # init the class members
        self.func_namespace = None  # 用户函数所在的命名空间
        self.func_name = None  # 用户函数名称
        self.func_updateTime = None  # 函数最近更新的时间
        self.userfunc = None  # 用户函数句柄
        self.metric_handler = None  # 埋点上报句柄
        self.kafkaProducer_handler = None  # kafka 生产客户端
        self.redis_handler = None  # redis 客户端句柄
        self.configs = {}  # 函数configmap信息
        self.secrets = {}  # 函数secrets信息
        self.cache = None  # Cache() # pod 周期级缓存对象
        logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)  # 设置日志的默认级别，在加载函数时会根据用户的环境变量进行修改

        info = read_func_info()
        self.func_namespace = "{}-{}".format(info.get("pn", "unknown"), info.get("mn", "unknown"))
        self.func_name = info.get("fn", "unknown")

        assert len(self.func_name) != 0 and len(self.func_namespace) != 0

        # get configs and secrets
        self.configs = read_config(PATH_CONFIGS, self.func_namespace, self.func_name)
        self.secrets = read_config(PATH_SECRETS, self.func_namespace, self.func_name)

        self.func_updateTime = str(time.time())

        # 设置日志级别
        self.set_logger_level()
        # 设置prometheus客户端
        self.set_prometheus_client()
        # 设置kafka客户端
        self.set_kafka_client()
        # 设置redis客户端
        self.set_redis_client()
        # 设置缓存
        self.set_cache()

    def set_logger_level(self):
        """set logger level"""
        logger_level = self.configs.get(LOCAL_CONFIG_KEY, {}).get("logger_level", "debug")
        level = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warn": logging.WARN,
            "error": logging.ERROR
        }.get(logger_level, logging.DEBUG)
        self.logger.debug("logger level will be {}".format(logger_level))
        # logging.basicConfig(level=level)
        self.logger.setLevel(level)

    def set_prometheus_client(self):
        """set prometheus client. The default is enable it."""
        if self.configs.get(LOCAL_CONFIG_KEY, {}).get("prometheus-enabled", "y") == "n":
            self.logger.debug("the prometheus client will not be created")
            return
        pushgateway_url = self.configs.get(LOCAL_CONFIG_KEY, {}).get("pushgateway-url", "")
        if len(pushgateway_url) == 0:
            pushgateway_url = self.configs.get(GLOBAL_CONFIG_KEY, {}).get("pushgateway-url", "")
        if len(pushgateway_url) == 0:
            pushgateway_url = PUSHGATEWAY_URL_DEFAULT
        prefix = self.func_namespace + "_" + self.func_name
        self.logger.debug("pushgateway_url is {}, prefix is {}, update_time is {}".format(pushgateway_url, prefix, self.func_updateTime))
        self.metric_handler = PrometheusForFission(prefix, self.func_updateTime, pushgateway_url, self.logger)

    def set_kafka_client(self):
        """set kafka client. The default is disable it."""
        if self.configs.get(LOCAL_CONFIG_KEY, {}).get("kafka-enabled", "n") == "n":
            self.logger.debug("the kafka producer will not be created")
            return
        kafka_broker_list = self.configs.get(LOCAL_CONFIG_KEY, {}).get("kafka-broker-list", "")
        if len(kafka_broker_list) == 0:
            kafka_broker_list = self.configs.get(GLOBAL_CONFIG_KEY, {}).get("kafka-broker-list", "")
        self.logger.debug("the kafka producer will connect to {}".format(kafka_broker_list))
        self.kafkaProducer_handler = KafkaProducer(bootstrap_servers=kafka_broker_list)

    def set_redis_client(self):
        """set redis client. The default is disable it."""
        if self.configs.get(LOCAL_CONFIG_KEY, {}).get("redis-enabled", "n") == "n":
            self.logger.debug("the redis client will not be created")
            return
        redis_url = self.configs.get(LOCAL_CONFIG_KEY, {}).get("redis-url", "")
        if len(redis_url) == 0:
            redis_url = self.configs.get(GLOBAL_CONFIG_KEY, {}).get("redis-url", "")
        self.logger.debug("the redis client will connect to {}".format(redis_url))
        self.redis_handler = redis.StrictRedis.from_url(redis_url)

    def set_cache(self):
        """set cache. The default is enable it"""
        if self.configs.get(LOCAL_CONFIG_KEY, {}).get("podcache-enabled", "y") == "n":
            self.logger.debug("the cache will not be created")
            return
        self.cache = Cache()

