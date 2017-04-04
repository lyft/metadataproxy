# bash needed for pipefail
SHELL := /bin/bash

APP_NAME := metadataproxy

ifneq ($(shell which brew),)
	VIRTUALENV_PATH = $(HOME)/.virtualenvs/$(APP_NAME)
endif

ifdef WORKON_HOME
	VIRTUALENV_PATH = $(WORKON_HOME)/$(APP_NAME)
endif

ifdef VIRTUAL_ENV
	VIRTUALENV_PATH = $(VIRTUAL_ENV)
endif

ifneq ($(wildcard .heroku/python/bin/python),)
	VIRTUALENV_PATH = .heroku/python
endif

ifndef VIRTUALENV_PATH
	VIRTUALENV_PATH = .virtualenv
endif
VIRTUALENV_BIN = $(VIRTUALENV_PATH)/bin

PYTHON = $(ENV) $(VIRTUALENV_BIN)/python

test: test_lint test_unit

test_lint:
	mkdir -p build
	set -o pipefail; flake8 | sed "s#^\./##" > build/flake8.txt || (cat build/flake8.txt && exit 1)

test_unit:
	# Disabled for now. We need to fully mock AWS calls.
	echo nosetests tests/unit

.PHONY: server
server: ## starts the built-in server
	export DEBUG=1 && $(PYTHON) wsgi.py
