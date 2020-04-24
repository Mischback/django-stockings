
run: django/runserver
commit: black isort flake

# ##### utility commands
black:
	tox -q -e black -- --diff

black/full:
	tox -q -e black

flake:
	tox -q -e util -- flake8 .

isort:
	tox -q -e util -- isort . --recursive --diff

isort/full:
	tox -q -e util -- isort . --recursive

# ##### Django commands

# Runs commands using a tox environment
django_cmd ?= version
django:
	tox -q -e django -- $(django_cmd)

# django-admin check
django/check:
	$(MAKE) django django_cmd="check"

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

.PHONY: \
	run \
	django \
	django/check django/migrate django/runserver django/shell
.SILENT:
