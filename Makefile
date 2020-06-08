project_name = "jingtao"
module_name = "play"

env_name = "python"
env_ns = "default"

func_name = "request"
func_ns = $(project_name)-$(module_name)

trigger_ns = $(func_ns)
http_method = "POST"

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