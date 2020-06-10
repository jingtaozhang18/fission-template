project_name = {{cookiecutter.project_name}}
module_name = {{cookiecutter.module_name}}

env_name = {{cookiecutter.env_name}}
env_ns = {{cookiecutter.env_ns}}

func_name = {{cookiecutter.func_name}}
func_ns = $(project_name)-$(module_name)

trigger_ns = $(func_ns)
http_method = {{cookiecutter.http_method}}

publish: package_source_code create_func create_http_trigger

create_func:
	fission function create --entrypoint "main.main" --buildcmd "./src/build.sh" --name $(func_name) --fns $(func_ns) \
							--env $(env_name) --envns $(env_ns) --src func.zip

update_func: package_source_code
	fission function update --entrypoint "main.main" --buildcmd "./src/build.sh" --name $(func_name) --fns $(func_ns) \
							--env $(env_name) --envns $(env_ns) --src func.zip

create_http_trigger:
	fission httptrigger create --function $(func_name) --fns $(func_ns) \
							   --url $(func_ns)/$(func_name)/default \
							   --method $(http_method) \
							   --name $(func_name)-default

test_func:
	fission fn test --name $(func_name) --fns $(func_ns)

package_source_code:
	zip -rq func.zip src

remove_fission_source:
	fission function delete --name $(func_name) --fns $(func_ns)
	fission httptrigger delete --name $(func_name)-default --triggerns $(func_ns)


clean:
	rm -f func.zip