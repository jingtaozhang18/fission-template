## Fission Python 函数提交模板

### 概念介绍
该模板可以用于提交Python版本的函数，提交之后将会由Fission进行托管维护。一个函数由三部分组成：
* 运行环境
* 代码
* 触发器

其中的运行环境将会由基础设施组的同学进行运维，业务同学只需要指定使用基础设施组提供的运行环境即可。代码部分是函数的主要逻辑，其参数输入是Flask的一个request请求，输出需要转换成字符串结构。触发器是触发函数的组件，目前模板支持的是HTTP方式的触发器，即通过URL链接，即可调用部署在集群中的函数代码。


在编写一个函数的时候，首先需要定位函数所属的`Project`和`Module`，然后再是函数名称`Func`。在脚本提交过程中，会将函数提交到`Project-Module`的命名空间下，您一定可以将资源提交到该命名空间下，但不一定能通过kubectl来获取该命名空间中的内容。

### 结构介绍
所有的函数代码都放在src文件夹下。主要由如下部分组成：

* `main.py`文件，其内的`main`函数是函数调用的入口，HTTP请求的输入可以从request中读取到。
* `requirements.txt`是项目需要的依赖
* `build.sh`是项目的编译脚本，您可以跟需要进行更改

### Makefile脚本

#### 参数介绍

##### 用户需要填写参数
* `item_name` 项目创建在本地时文件夹的名字
* `project_name`  项目名称
* `module_name` 模块名称
* `env_name` 运行环境的名称，目前支持`python`和`python-pillow`两个
* `env_ns` 运行环境所在的命名空间，暂时均在default下
* `func_name` 函数名称
* `http_method` HTTP触发器的方法，可选项`GET|POST|PUT|DELETE|HEAD`
* `topic_name` 若使用消息队列进行触发的话，可以填此配置
* `cron_setting` 定时任务触发策略 `* * * * * ?` 或者 `@midnight`，`@every 1h30m`
* `cron_param` 定时任务触发时，携带的参数，必须是json类型，注意转义字符

##### 自动生成的参数
* `func_ns = $(project_name)-$(module_name)` 函数将会提交到`$(func_ns)`的命名空间中。
* `trigger_ns = $(func_ns)` 触发器所在的命名空间，默认和函数的命名空间一样
* `http_trigger_name = $(func_name)-http` HTTP触发器名称
* `mq_trigger_name = $(func_name)-mq` 消息队列触发器名称
* `time_trigger_name = $(func_name)-time` 定时任务触发器名称

#### 命令介绍
* `make publish` 会直接将函数提交到集群中，并且会自动创建http-trigger，可以根据需求，修改publish的执行任务
* `make create_func` 创建函数，会自动打包代码，并提交configmap和secrets的配置
* `make create_http_trigger` 创建http请求的触发器
* `make create_mq_trigger` 添加消息队列的触发，消费$(topic-name)中的消息，并将结果上传到到`$(func_ns)-$(func_name)-response`的topic中，处理错误的上传到`$(func_ns)-$(func_name)-error`的topic中，您可以通过删除命令中配置的`resptopic`和`errortopic`项来取消对应的上传。
* `make create_cron_trigger` 创建定时任务触发器
* `make apply_func_config` 更新configmap和secrets的配置
* `make update_func` 更新函数，会自动打包代码，并提交configmap和secrets的配置
* `make update_mq_trigger` 更新消息队列触发，多用于修改所要消费的topic
* `make update_cron_trigger` 更新定时任务触发器
* `make see_log` 查看函数日志，默认展示执行了这个命令后的函数日志，**需要使用开发机上的`/usr/local/bin`目录下的fission命令，若执行出错，请先`which fission`检查fission命令是否是`/usr/local/bin`下的fission**
* `make remove_func` 删除函数
* `make remove_http_trigger` 删除HTTP触发器
* `make remove_mq_trigger` 删除消息队列触发，**慎用**。删除触发就相当于放弃了原来的消费组号，可能导致队列中的消息有遗漏处理的情况。
* `make remove_cron_trigger` 删除定时任务触发器
* `make package_source_code` 打包函数，会自动调用清理包的命令，保证打包干净
* `make clean` 清理本地打包

### 使用模板创建自己的项目
``` bash
cookiecutter https://git.huxiang.pro/base/fission/fission-template.git 或者
cookiecutter git@git.huxiang.pro:base/fission/fission-template.git
```

### 在本地调试您的项目
为了方便用户在本地调试自己的项目，

#### 模拟需要的文件
您的项目下有几个文件是专门为本地调试而生成的：
* `fake-fission-secret-configmap.yaml` 在本地调试时使用的fission全局配置，您可以根据本地测试环境改写该文件
* `src/fake_environment.py` 在本地调试时，模拟环境由该文件生成，正常情况下您不需要更改此文件，如有无法解决的报错，请联系项目维护员

#### 模拟需要的包
在fission环境中，使用了一些定制版的包，暂时不支持官方途径安装，您需要按照如下命令，进行手动配置
```bash
# 为fission定制的prometheus client python版
git clone https://git.jingtao.fun/jingtao/prometheus_client_python.git
cd prometheus_client_python && python setup.py install
```

#### 启用模拟
在模拟环境和真实环境之间，是通过环境变量`fission_local`的y或者n来决定，当您设置环境变量fission_local为y时，就会启用模拟环境。
模拟环境暂时不支持模拟post请求接入过程，因此您在main方法中通过`flask_request`获取内容的代码需要手动更改。