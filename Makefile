gitrev := $(shell git rev-parse --short=10 HEAD)
VENV_NAME := venv
now := $(shell date --utc +%Y%m%dT%H%MZ)
github3_version:=1.1.0-$(now)-$(gitrev)
port := 8888
image_to_use := offboard-slim
container_user_name := jovyan
SOPS_credentials := $(SECOPS_SOPS_PATH)/off-boarding.yaml

DOCKER_OPTS :=

.PHONY: help
help:
	@echo "Targets available"
	@echo ""
	@echo "    help          this message"
	@echo "    build         create a docker image based on working directory"
	@echo "    run           run a docker image previously created"
	@echo "    run-edit      run with modifiable current directory"
	@echo "    vscode        set env vars, then launch vscode"
	@echo "    jupyter       run local (non docker) jupyter server for development (deprecated)"
	@echo "    $(VENV_NAME)  create a local virtualenv for old style development (deprecated)"

$(VENV_NAME):
	python3 -m venv $@
	. $(VENV_NAME)/bin/activate && echo req*.txt | xargs -n1 pip install -r
	@echo "Virtualenv created in $(VENV_NAME). You must activate before continuing."
	false

SHELL := /bin/bash
.PHONY: build debug_build
# New build
build: Dockerfile .dockerignore Makefile notebooks/*ipynb requirements*.txt
	docker build --tag $(image_to_use):$(github3_version) --tag $(image_to_use):latest .
# debug the build by not using buildkit - we also assume last one failed, so no need to tag prior
debug-build:
	DOCKER_BUILDKIT=0 docker build --tag $(image_to_use):debug .

# For `run`, we use the configs baked into the image at the time of
# the build, so we get what we expect.
.PHONY: run
run:
	$(SHELL) -ce ' ( source set_secrets_in_env.sh $(SOPS_credentials); \
		export TZ=$$(./get_olson_tz.sh) ; \
		docker run --rm --publish-all \
			--env "GITHUB_PAT" \
			--env "CIS_CLIENT_ID" \
			--env "CIS_CLIENT_SECRET" \
			--env "TZ" \
			--env "DOCKER_STACKS_JUPYTER_CMD=notebook" \
			--publish $(port):8888 \
			$(image_to_use):latest \
		& \
		job_pid=$$! ; \
		sleep 5 ; \
		docker ps --filter "ancestor=$(image_to_use)" ; \
		wait $$job_pid ; \
	) '

# For `run-edit`, we're mapping the local notebooks directory onto the container's notebooks directory
# This allows for editing the notebook, but still uses the baked in jupyter configuration (in $HOME)

.PHONY: run-edit
run-edit:
	$(SHELL) -ce ' ( source set_secrets_in_env.sh $(SOPS_credentials); \
		export TZ=$$(./get_olson_tz.sh) ; \
		docker run --rm --publish-all \
			$(DOCKER_OPTS) \
			--env "GITHUB_PAT" \
			--env "CIS_CLIENT_ID" \
			--env "CIS_CLIENT_SECRET" \
			--env "TZ" \
			--env "DOCKER_STACKS_JUPYTER_CMD=notebook" \
			--publish $(port):8888 \
			--volume "$$PWD/notebooks:/home/$(container_user_name)"/notebooks \
			$(image_to_use):latest \
		& \
		job_pid=$$! ; \
		sleep 10 ; \
		docker ps --filter "ancestor=$(image_to_use):$(github3_version)" ; \
		wait $$job_pid ; \
	) '

.PHONY: vscode
vscode:
	$(SHELL) -cex ' ( source set_secrets_in_env.sh $(SOPS_credentials); \
		export TZ=$$(./get_olson_tz.sh) ; \
		code . \
	) '

.PHONY: jupyter
jupyter:
	$(SHELL) -ce ' ( source set_secrets_in_env.sh $(SOPS_credentials); \
		jupyter-notebook ; \
	) '

.PHONY: debug-edit
debug-edit:
	$(MAKE) DOCKER_OPTS="--security-opt=seccomp:unconfined" run-edit


# vim: noet ts=8
