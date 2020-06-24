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

* `project_name`  项目名称
* `module_name` 模块名称
* `env_name` 运行环境的名称，目前支持`python`和`python-pillow`两个
* `env_ns` 运行环境所在的命名空间，暂时均在default下
* `func_name` 函数名称
* `func_ns = $(project_name)-$(module_name)` 函数将会提交到`$(func_ns)`的命名空间中。
* `trigger_ns = $(func_ns)` 触发器所在的命名空间，默认和函数的命名空间一样
* `http_method` HTTP触发器的方法，可选项`GET|POST|PUT|DELETE|HEAD`
* `topic-name` 若使用消息队列进行触发的话，可以填此配置

#### 命令介绍
* `make publish` 会直接将函数提交到集群中，并且会自动创建http-trigger，**但不会创建mq-trigger**。
* `make create_mq_trigger` 添加消息队列的触发，消费$(topic-name)中的消息，并将结果上传到到`$(func_ns)-$(func_name)-response`的topic中，处理错误的上传到`$(func_ns)-$(func_name)-error`的topic中，您可以通过删除命令中配置的`resptopic`和`errortopic`项来取消对应的上传。
* `make update_func` 更新函数
* `make update_mq_trigger` 更新消息队列触发，多用于修改所要消费的topic
* `make see_log` 查看函数日志，默认展示执行了这个命令后的函数日志，**需要使用开发机上的`/usr/local/bin`目录下的fission命令，若执行出错，请先`which fission`检查fission命令是否是`/usr/local/bin`下的fission**
* `make remove_func_and_http_trigger` 会将创建的**函数**和**http-trigger**删除掉，**但不会删除mq-trigger**
* `make remove_mq_trigger` 删除消息队列触发，**慎用**。删除触发就相当于放弃了原来的消费组号，可能导致队列中的消息有遗漏处理的情况。

### 使用模板创建自己的项目
``` bash
cookiecutter https://git.huxiang.pro/base/fission/fission-template.git 或者
cookiecutter git@git.huxiang.pro:base/fission/fission-template.git
```

模板中的`item_name`是创建在本地文件夹的名字