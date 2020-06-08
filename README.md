## Fission Python 函数提交模板

### 概念介绍
在编写一个函数的时候，首先需要定位函数所属的`Project`和`Module`，然后再是函数名称`Func`。在脚本提交过程中，会将函数提交到`Project-Module`的命名空间下，您需要确认您有该命名空间的权限。

### 结构介绍
所有的函数代码都放在src文件夹下

### Makefile脚本
`make publish` 会直接将函数提交到集群中，并且会自动创建http-trigger
`make remove_fission_source` 会将创建的函数和trigger删除掉
