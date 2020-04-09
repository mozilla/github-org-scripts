VENV_NAME=venv
github3_version=1.1.0

.PHONY: help
help:
	@echo "Targets available"
	@echo ""
	@echo "    help          this message"
	@echo "    dev           create & run a docker image based on working directory"
	@echo "    $(VENV_NAME)  create a local virtualenv for old style development"

$(VENV_NAME):
	virtualenv --python=python2.7 $@
	. $(VENV_NAME)/bin/activate && echo req*.txt | xargs -n1 pip install -r
	@echo "Virtualenv created in $(VENV_NAME). You must activate before continuing."
	false

SHELL := /bin/bash
.PHONY: dev
# see https://github.com/jupyter/repo2docker/issues/871 for why the
# secret is in the output
dev:
	$(SHELL) -c ' ( export GITHUB_PAT=$$(pass show Mozilla/moz-hwine-PAT) ; \
		[[ -z $GITHUB_PAT ]] && exit 3 ; \
		repo2docker --image-name "dev:$(github3_version)" \
			--env "GITHUB_PAT=$$GITHUB_PAT" \
			--editable \
			. \
		; \
	) '
	@echo "Secrets Above -- clear screen"


# vim: noet ts=8
