VENV_NAME=venv
github3_version=1.1.0

.PHONY: help
help:
	@echo "Targets available"
	@echo ""
	@echo "    help          this message"
	@echo "    dev           create & run a docker image based on working directory"
	@echo "    run-dev       run a docker image previously created"
	@echo "    run-update    run with modifiable current directory"
	@echo "    $(VENV_NAME)  create a local virtualenv for old style development"

$(VENV_NAME):
	virtualenv --python=python2.7 $@
	. $(VENV_NAME)/bin/activate && echo req*.txt | xargs -n1 pip install -r
	@echo "Virtualenv created in $(VENV_NAME). You must activate before continuing."
	false

SHELL := /bin/bash
.PHONY: dev
dev:
	-docker rmi dev:$(github3_version)
	$(SHELL) -c ' ( export GITHUB_PAT=$$(pass show Mozilla/moz-hwine-PAT) ; \
		[[ -z $GITHUB_PAT ]] && exit 3 ; \
		repo2docker --image-name "dev:$(github3_version)" \
			--env "GITHUB_PAT" \
			--editable \
			. \
		; \
	) '

.PHONY: run-dev
run-dev:
	$(SHELL) -c ' ( export GITHUB_PAT=$$(pass show Mozilla/moz-hwine-PAT) ; \
		[[ -z $GITHUB_PAT ]] && exit 3 ; \
		docker run --rm --publish-all \
			--env "GITHUB_PAT" \
			dev:$(github3_version) \
		& \
		job_pid=$$! ; \
		sleep 5 ; \
		docker ps --filter "ancestor=dev:1.1.0" ; \
		wait $$job_pid ; \
	) '

.PHONY: run-update
run-update:
	$(SHELL) -c ' ( export GITHUB_PAT=$$(pass show Mozilla/moz-hwine-PAT) ; \
		[[ -z $GITHUB_PAT ]] && exit 3 ; \
		docker run --rm --publish-all \
			--env "GITHUB_PAT" \
			--volume "$$PWD:/home/$$USER" \
			dev:$(github3_version) \
		& \
		job_pid=$$! ; \
		sleep 5 ; \
		docker ps --filter "ancestor=dev:1.1.0" ; \
		wait $$job_pid ; \
	) '


# vim: noet ts=8
