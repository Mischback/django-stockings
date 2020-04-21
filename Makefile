
run: django/runserver

# ##### utility commands
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

# django-admin createsuperuser
django/createsuperuser: django/migrate
	$(MAKE) django django_cmd="createsuperuser"

# django-admin migrate -v 0
django/migrate:
	$(MAKE) django django_cmd="migrate -v 0"

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
	django/check django/createsuperuser django/migrate django/runserver \
	django/shell
.SILENT:
