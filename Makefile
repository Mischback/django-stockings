
doc: sphinx/serve/html
run: django/runserver

# ##### utility commands
bandit:
	$(MAKE) pre-commit pre-commit_id="bandit"

black:
	$(MAKE) pre-commit pre-commit_id="black"

clean:
	- tox -q -e util -- coverage erase
	rm -rf docs/build/*
	find . -iname "*.pyc" -delete
	find . -iname "__pycache__" -delete
	find . -iname ".coverage.*" -delete

coverage: clean test
	- tox -q -e util -- coverage combine
	tox -q -e util -- coverage report

flake: flake8
flake8:
	$(MAKE) pre-commit pre-commit_id="flake8"

isort:
	$(MAKE) pre-commit pre-commit_id="isort"

pre-commit_id ?= ""
pre-commit:
	tox -q -e util -- pre-commit run $(pre-commit_id)

test_cmd ?= ""
test:
	tox -q -e testing -- $(test_cmd)

test_tag ?= current
test/tag:
	$(MAKE) test test_cmd="-t $(test_tag)"

test/time:
	$(MAKE) test test_cmd="--time"

# ##### Django commands

# Runs commands using a tox environment
django_cmd ?= version
django:
	tox -q -e django -- $(django_cmd)

# django-admin check
django/check:
	$(MAKE) django django_cmd="check"

# django-admin createsuperuser
django/createsuperuser:
	tox -q -e djangosuperuser

# django-admin makemigrations
django/makemigrations:
	$(MAKE) django django_cmd="makemigrations stockings"

# django-admin migrate -v 0
django/migrate:
	$(MAKE) django django_cmd="migrate"

# django-admin runserver 0:8080
host_port ?= 0:8080
django/runserver: django/migrate
	$(MAKE) django django_cmd="runserver $(host_port)"

# django-admin shell
django/shell:
	$(MAKE) django django_cmd="shell"

sphinx/build/html:
	tox -q -e sphinx

sphinx/build/apidoc:
	tox -q -e sphinx -- sphinx-apidoc -o source/api stockings */migrations/* --tocfile api --separate

sphinx/serve/html: sphinx/build/html
	tox -q -e sphinx-srv

.PHONY: \
	run \
	bandit black clean coverage flake flake8 isort pre-commit test test/tag test/time \
	django \
	django/check django/createsuperuser django/makemigrations django/migrate \
	django/runserver django/shell
.SILENT:
