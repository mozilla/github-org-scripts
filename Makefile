VENV_NAME=venv

$(VENV_NAME):
	virtualenv --python=python2.7 $@
	. $(VENV_NAME)/bin/activate && echo req*.txt | xargs -n1 pip install -r
	@echo "Virtualenv created in $(VENV_NAME). You must activate before continuing."
	false

1.0a4:
	repo2docker --image-name 'github-org-script:1.0a4' \
		    --ref repo2docker \
		    https://github.com/hwine/github-org-scripts \

# vim: noet ts=8
