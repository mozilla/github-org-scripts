VENV_NAME:=venv
github3_version:=1.1.1
port := 10001
image_to_use := offboard-py2

DOCKER_OPTS :=

.PHONY: help
help:
	@echo "Targets available"
	@echo ""
	@echo "    help          this message"
	@echo "    build         create a docker image based on working directory"
	@echo "    run-dev       run a docker image previously created"
	@echo "    run-update    run with modifiable current directory"
	@echo "    $(VENV_NAME)  create a local virtualenv for old style development"

$(VENV_NAME):
	virtualenv --python=python3.7 $@
	. $(VENV_NAME)/bin/activate && echo req*.txt | xargs -n1 pip install -r
	@echo "Virtualenv created in $(VENV_NAME). You must activate before continuing."
	false

SHELL := /bin/bash
.PHONY: build
build: jupyter-config
	-docker rmi $(image_to_use):$(github3_version) 2>/dev/null
	$(SHELL) -c '  \
		repo2docker --image-name "$(image_to_use):$(github3_version)" \
			--no-run \
			. \
		; \
	'

.PHONY: run-dev
run-dev:
	$(SHELL) -c ' ( export GITHUB_PAT=$$(pass show Mozilla/moz-hwine-PAT) ; \
		[[ -z $$GITHUB_PAT ]] && exit 3 ; \
		export CIS_CLIENT_ID=$$(pass show Mozilla/person_api_client_id 2>/dev/null) ; \
		export CIS_CLIENT_SECRET=$$(pass show Mozilla/person_api_client_secret 2>/dev/null) ; \
		docker run --rm --publish-all \
			--env "GITHUB_PAT" \
			--env "CIS_CLIENT_ID" \
			--env "CIS_CLIENT_SECRET" \
			--publish $(port):8888 \
			$(image_to_use):$(github3_version) \
		& \
		job_pid=$$! ; \
		sleep 5 ; \
		docker ps --filter "ancestor=$(image_to_use):$(github3_version)" ; \
		wait $$job_pid ; \
	) '

.PHONY: run-update
run-update: jupyter-config
	$(SHELL) -c ' ( export GITHUB_PAT=$$(pass show Mozilla/moz-hwine-PAT) ; \
		[[ -z $$GITHUB_PAT ]] && exit 3 ; \
		export CIS_CLIENT_ID=$$(pass show Mozilla/person_api_client_id 2>/dev/null) ; \
		export CIS_CLIENT_SECRET=$$(pass show Mozilla/person_api_client_secret 2>/dev/null) ; \
		docker run --rm --publish-all \
			$(DOCKER_OPTS) \
			--env "GITHUB_PAT" \
			--env "CIS_CLIENT_ID" \
			--env "CIS_CLIENT_SECRET" \
			--publish $(port):8888 \
			--volume "$$PWD:/home/$$USER" \
			$(image_to_use):$(github3_version) \
		& \
		job_pid=$$! ; \
		sleep 5 ; \
		docker ps --filter "ancestor=$(image_to_use):$(github3_version)" ; \
		wait $$job_pid ; \
	) '

.PHONY: debug-update
debug-update:
	$(MAKE) DOCKER_OPTS="--security-opt=seccomp:unconfined" run-update

jupyter-config: .jupyter/jupyter_notebook_config.py
.jupyter/jupyter_notebook_config.py:
	echo -e >$@ \
"# disable browser launch (it's in a container)\n"\
"c.NotebookApp.open_browser = False\n"\
"# Set connection string\n"\
"c.NotebookApp.portInt = $(port)\n"\
"c.NotebookApp.custom_display_url = 'http://localhost:$(port)'\n"\
"# disable security locally\n"\
"c.NotebookApp.token = ''\n"\
"c.NotebookApp.password = ''"

# vim: noet ts=8
