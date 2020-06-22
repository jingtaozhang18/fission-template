project_name = {{cookiecutter.project_name}}
module_name = {{cookiecutter.module_name}}

env_name = {{cookiecutter.env_name}}
env_ns = {{cookiecutter.env_ns}}

func_name = {{cookiecutter.func_name}}
func_ns = $(project_name)-$(module_name)

trigger_ns = $(func_ns)
http_method = {{cookiecutter.http_method}}

topic_name = {{cookiecutter.topic_name}}  # todo 如果需要使用消息队列触发，请修改这里

fission_namespace = "fission"

publish: package_source_code create_func create_http_trigger

create_func:
	FISSION_NAMESPACE=$(fission_namespace) fission function create --entrypoint "main.main" --buildcmd "./src/build.sh" --name $(func_name) --fns $(func_ns) \
							--env $(env_name) --envns $(env_ns) --src func.zip

update_func: package_source_code
	FISSION_NAMESPACE=$(fission_namespace) fission function update --entrypoint "main.main" --buildcmd "./src/build.sh" --name $(func_name) --fns $(func_ns) \
							--env $(env_name) --envns $(env_ns) --src func.zip

create_http_trigger:
	FISSION_NAMESPACE=$(fission_namespace) fission httptrigger create --function $(func_name) --fns $(func_ns) \
							   --url $(func_ns)/$(func_name) \
							   --method $(http_method) \
							   --name $(func_name)-http

create_mqtrigger:
	FISSION_NAMESPACE=$(fission_namespace) fission mqtrigger create --name $(func_name)-mq --topic $(topic_name) \
		--resptopic $(func_ns)-$(func_name)-response --errortopic $(func_ns)-$(func_name)-error \
		--contenttype "application/json" --maxretries 3 \
		--mqtype kafka --function $(func_name) --fns  $(func_ns)

test_func:
	FISSION_NAMESPACE=$(fission_namespace) fission fn test --name $(func_name) --fns $(func_ns)

package_source_code:
	zip -rq func.zip src

remove_fission_source:
	FISSION_NAMESPACE=$(fission_namespace) fission function delete --name $(func_name) --fns $(func_ns)
	FISSION_NAMESPACE=$(fission_namespace) fission httptrigger delete --name $(func_name)-default --triggerns $(func_ns)

clean:
	rm -f func.zip