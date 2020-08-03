project_name = {{cookiecutter.project_name}}
module_name = {{cookiecutter.module_name}}

env_name = {{cookiecutter.env_name}}
env_ns = {{cookiecutter.env_ns}}

func_name = {{cookiecutter.func_name}}

http_method = {{cookiecutter.http_method}}

topic_name = {{cookiecutter.topic_name}}

cron_setting = {{cookiecutter.cron_setting}}

# 一定是字典结构
cron_param = {}

# 默认生成的函数命名空间、触发器的命名空间、HTTP Triger 名称，以及 MQ Trigger 名称
func_ns = $(project_name)-$(module_name)
trigger_ns = $(func_ns)
http_trigger_name = $(func_name)-http
mq_trigger_name = $(func_name)-mq
time_trigger_name = $(func_name)-time

# 允许函数空闲时长
idletimeout = 120
# 允许函数执行的时长
fntimeout = 60
# fission controller 组件所在的命名空间
fission_namespace = "fission"

publish: create_func create_http_trigger

create_func: package_source_code apply_func_config
	FISSION_NAMESPACE=$(fission_namespace) fission function create --entrypoint "main.main" --buildcmd "./src/build.sh" --name $(func_name) --fns $(func_ns) \
							--env $(env_name) --envns $(env_ns) --src func.zip --fntimeout $(fntimeout) --idletimeout $(idletimeout) \
							--configmap fission-secret-configmap.fission-function-global-configmap --configmap func-$(func_name)

create_http_trigger:
	FISSION_NAMESPACE=$(fission_namespace) fission httptrigger create --function $(func_name) --fns $(func_ns) \
							   --url $(func_ns)/$(func_name) \
							   --method $(http_method) \
							   --name $(http_trigger_name)
	echo "your httptrigger path is $(func_ns)/$(func_name)"

create_mq_trigger:
	FISSION_NAMESPACE=$(fission_namespace) fission mqtrigger create --name $(mq_trigger_name) --topic $(topic_name) \
		--resptopic $(func_ns)-$(func_name)-response --errortopic $(func_ns)-$(func_name)-error \
		--contenttype "application/json" --maxretries 3 \
		--mqtype kafka --function $(func_name) --fns $(func_ns)

create_cron_trigger:
	FISSION_NAMESPACE=$(fission_namespace) fission timetrigger create --cron "$(cron_setting)" --function $(func_name) \
		--name $(time_trigger_name) --fns $(func_ns) --param $(cron_param)

apply_func_config:
	kubectl apply -f func-config.yaml

update_func: package_source_code apply_func_config
	FISSION_NAMESPACE=$(fission_namespace) fission function update --entrypoint "main.main" --buildcmd "./src/build.sh" --name $(func_name) --fns $(func_ns) \
							--env $(env_name) --envns $(env_ns) --src func.zip --fntimeout $(fntimeout) --idletimeout $(idletimeout) \
							--configmap fission-secret-configmap.fission-function-global-configmap --configmap func-$(func_name)

update_mq_trigger:
	# 若不需要resptopic和errortopic, 请自行删除这两个配置
	FISSION_NAMESPACE=$(fission_namespace) fission mqtrigger update --name $(mq_trigger_name) --topic $(topic_name) \
		--resptopic $(func_ns)-$(func_name)-response --errortopic $(func_ns)-$(func_name)-error \
		--contenttype "application/json" --maxretries 3 \
		--function $(func_name) --triggerns $(trigger_ns)

update_cron_trigger:
	FISSION_NAMESPACE=$(fission_namespace) fission timetrigger update --cron "$(cron_setting)" --function $(func_name) \
		--name $(time_trigger_name) --triggerns $(trigger_ns) --param $(cron_param)

test_func:
	FISSION_NAMESPACE=$(fission_namespace) fission fn test --name $(func_name) --fns $(func_ns)

see_log:
	# 参数n 是从最新位置开始打印日志，若需要查看之前的日志，请删掉n
	FISSION_NAMESPACE=$(fission_namespace) fission fn log --name $(func_name) --fns $(func_ns) -fn

package_source_code: clean
	zip -rq func.zip src

remove_func:
	FISSION_NAMESPACE=$(fission_namespace) fission function delete --name $(func_name) --fns $(func_ns)

remove_http_trigger:
	FISSION_NAMESPACE=$(fission_namespace) fission httptrigger delete --name $(http_trigger_name) --triggerns $(trigger_ns)

remove_mq_trigger:
	FISSION_NAMESPACE=$(fission_namespace) fission mqtrigger delete --name $(mq_trigger_name) --triggerns $(trigger_ns)

remove_cron_trigger:
	FISSION_NAMESPACE=$(fission_namespace) fission timetrigger delete --name $(time_trigger_name) --triggerns $(trigger_ns)

clean:
	rm -f func.zip