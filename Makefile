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
	venv/bin/pip install -r requirements.txt > /dev/null
	venv/bin/pip install pyinstaller
	venv/bin/pyinstaller --paths "venv/lib/python3.*/site-packages" --bootloader-ignore-signals -y ssm.py
	@echo -e "$(GREEN)✅ Done.$(RESET)"

##@ Install

install: ## Install the CLI to /usr/local/bin
	@echo -e "$(GREEN)🔗 Installing 'ssm' command...$(RESET)"
	@cp -r dist/ssm/* /usr/local/bin
	@echo -e "$(GREEN)✅ Installed as 'ssm'$(RESET)"

uninstall: ## Remove the CLI from /usr/local/bin
	@echo -e "$(YELLOW)🧹 Removing 'ssm' from /usr/local/bin...$(RESET)"
	@rm -f /usr/local/bin/ssm
	@rm -f /usr/local/bin/_internal
	@echo -e "$(GREEN)✅ Uninstalled$(RESET)"

##@ Docker

run/docker: ## Run the tool inside a Docker container (Ubuntu + Python)
	@echo -e "$(GREEN)🐳 Spinning up Ubuntu container...$(RESET)"
	docker run --name ssm-app -dit -v $$(pwd):/app -w /app ubuntu:20.04 bash
	docker exec -it ssm-app apt update
	docker exec -it ssm-app apt install -y python3 python3-pip python3-venv
	docker exec -it ssm-app bash

##@ Utility

clean: ## Removevenv and Python artifacts
	@echo -e "$(YELLOW)🧼 Cleaning up...$(RESET)"
	@rm -rf venv
	@rm -rf dist/ build/
	@rm -f ssm.spec
	@find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	@echo -e "$(GREEN)✅ Cleaned$(RESET)"
