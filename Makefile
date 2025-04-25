SHELL := /bin/bash

# Nice colors
YELLOW := \033[1;33m
GREEN := \033[0;32m
CYAN := \033[36m
RESET := \033[0m

.DEFAULT_GOAL := help

## Show this help menu
help:
	@echo -e "\n$(YELLOW)Usage:$(RESET)\n  make $(CYAN)<target>$(RESET)\n"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_\-\/]+:.*?##/ { \
		printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 \
	} /^##@/ { printf "\n\033[1;33m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Build

build: ## Create virtual environment and install dependencies
	@echo -e "$(YELLOW)🔧 Checking virtual environment...$(RESET)"
	@if [ ! -d "./venv" ]; then \
		echo -e "$(GREEN)📦 Creating venv...$(RESET)"; \
		python3 -m venv venv; \
	fi
	@echo -e "$(GREEN)📥 Installing dependencies...$(RESET)"
	venv/bin/pip install --upgrade pip > /dev/null
	venv/bin/pip install -r requirements.txt > /dev/null
	@echo -e "$(GREEN)✅ Done.$(RESET)"

##@ Install

install: ## Install the CLI to /usr/local/bin
	@echo -e "$(GREEN)🔗 Installing 'ssm' command...$(RESET)"
	@ln -sf $(PWD)/main.py /usr/local/bin/ssm
	@chmod +x /usr/local/bin/ssm
	@echo -e "$(GREEN)✅ Installed as 'ssm'$(RESET)"

uninstall: ## Remove the CLI from /usr/local/bin
	@echo -e "$(YELLOW)🧹 Removing 'ssm' from /usr/local/bin...$(RESET)"
	@rm -f /usr/local/bin/ssm
	@echo -e "$(GREEN)✅ Uninstalled$(RESET)"

##@ Docker

run/docker: ## Run the tool inside a Docker container (Ubuntu + Python)
	@echo -e "$(GREEN)🐳 Spinning up Ubuntu container...$(RESET)"
	docker run --rm --name ssm-test -it -v $$(pwd):/app -w /app python:3.11-slim bash

##@ Utility

clean: ## Removevenv and Python artifacts
	@echo -e "$(YELLOW)🧼 Cleaning up...$(RESET)"
	@rm -rf venv
	@find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	@echo -e "$(GREEN)✅ Cleaned$(RESET)"
