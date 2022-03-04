VENV_NAME:=venv
gitrev := $(shell git rev-parse --short=10 HEAD)
now := $(shell date --utc +%Y%m%dT%H%MZ)
github3_version:=1.1.0-$(now)-$(gitrev)
port := 10001
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
	@echo "    jupyter 	 run local (non docker) jupyter server for development"
	@echo "    $(VENV_NAME)  create a local virtualenv for old style development"

$(VENV_NAME):
	virtualenv --python=python3.7 $@
	. $(VENV_NAME)/bin/activate && echo req*.txt | xargs -n1 pip install -r
	@echo "Virtualenv created in $(VENV_NAME). You must activate before continuing."
	false

SHELL := /bin/bash
.PHONY: build debug_build
# New build
build:
	docker build --tag $(image_to_use):$(github3_version) --tag $(image_to_use):latest .
# debug the build by not using buildkit - we also assume last one failed, so no need to tag prior
debug_build:
	DOCKER_BUILDKIT=0 docker build --tag $(image_to_use):debug .
.PHONY: build-old
# we use a file url to avoid including work files in the production
# image. During development, you may prefer a bare dot "." to pick up
# local changes, and removethe `--ref ` option
build-old:
	-docker tag $(image_to_use):$(github3_version) $(image_to_use):$(github3_version)-previous 2>/dev/null
	$(SHELL) -c '  \
		repo2docker --image-name "$(image_to_use):$(github3_version)" \
			--user-name $(container_user_name) \
			--no-run \
			--ref $$(git show-ref --verify --hash --head HEAD) \
			file://$$PWD/.git \
		; \
	'

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

# For `run-edit`, we're mapping the current directory atop the home
# directory
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
			--publish $(port):8888 \
			--volume "$$PWD/notebooks:/home/$(container_user_name)/notebooks" \
			$(image_to_use):$(github3_version) \
		& \
		job_pid=$$! ; \
		sleep 5 ; \
		docker ps --filter "ancestor=$(image_to_use):$(github3_version)" ; \
		wait $$job_pid ; \
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
