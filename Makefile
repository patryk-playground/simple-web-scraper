conf ?= config.env
include $(conf)
export $(shell sed 's/=.*//' $(conf))

SHELL := /bin/bash

.PHONY: help generate-requirements publish container-config

.DEFAULT_GOAL := help

help:
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

generate-requirements: code-format ## Generate production dependencies
	@echo 'Create requirements file based on pipenv Pipfile content'
	@pipenv lock -r > requirements.txt

lint: code-format ## Check code with pylint
	@pipenv run pylint *.py

code-format: ## Format the code with Black auto-formatter
	@pipenv run black *.py

export-csv: ## Export CSV file
	@pipenv run python3 simple_scraper.py --filetype 'csv'

export-xml: ## Export XML file
	@pipenv run python3 simple_scraper.py --filetype 'xml'

export-xls: ## Export XLS file
	@pipenv run python3 simple_scraper.py --filetype 'xls'

export-all: export-csv export-xml export-xls ## Export all file formats
