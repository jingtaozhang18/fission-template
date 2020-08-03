# -*- coding: utf-8 -*-
from flask import request as flask_request
import json
from flask import g


def main():
    # 日志的输出级别和下面介绍的功能开关请在func-config.yaml文件中进行配置

    #  打日志
    # g.logger.info()

    #  打点
    # metric name 为埋点的名称
    # labels 为埋点的标签信息，为字典结构
    # g.metric_handler.counter("metric name", labels, 1)  # 通常用于统计频率信息等
    # g.metric_handler.gauge("metric name", labels, 1)  # 通常用于持续计数等

    #  读取configmap和secrets
    # configmap的信息存储在g.configs
    # secrets的信息存储在g.secrets
    # 全局配置使用 g.configs.get("global", {}).get(key, None)
    # 局部配置使用 g.configs.get("local", {}).get(key, None)
    # secrets的全局和局部配置和configs同理

    #  使用pod生命周期级别的缓存
    # g.cache
    # 线程安全，可以保证尽可能多的使用缓存，减少实际计算的次数
    # key 键
    # param 是传递给func的参数，目前仅支持单个参数
    # timeout 有效时间，为0,则永远有效
    # use_old 当键值过期，且func返回了None时，是否继续使用原来的旧值
    # old_time 如果使用原来的旧值，则旧值可以继续有效的时间
    # 返回func，或者func失败时缓存的旧值
    # 保证func短时间多次请求，func只会执行一次
    # g.cache.put(key, func=lambda x: x, param=None, timeout=0, use_old=False, old_timeout=30)
    #
    # no_delete 如果键失效是否不删除旧值
    # 返回缓存中的内容，如果没有命中或者失效返回None
    # g.cache.get(key, no_delete=False)
    #
    # 推荐用法，将get和put操作结合到了一起。参数含义如上
    # 返回func计算的或者缓存中的值
    # get_and_write(self, key: str, func=lambda x: x, param=None, timeout=0, use_old=True, old_timeout=30)
    #
    # 删除
    # def pop(self, key):

    #  kafka生产者句柄，投递消息到topic_name中
    # g.kafkaProducer_handler.send(topic_name, str.encode(msg))

    # 关于使用消息队列和定时任务触发时，读取输入的方法
    # 均是从flask_request.json变量中读取

    return json.dumps(flask_request.json)
