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

build-ssm: ## Build SSM CLI
	@echo -e "$(YELLOW)🔧 Building SSM CLI...$(RESET)"
	venv/bin/pyinstaller --paths "venv/lib/python3.*/site-packages" --bootloader-ignore-signals -y ssm.py
	@echo -e "$(GREEN)✅ SSM CLI built.$(RESET)"

build-ssmc: ## Build SSMC CLI
	@echo -e "$(YELLOW)🔧 Building SSMC CLI...$(RESET)"
	venv/bin/pyinstaller --paths "venv/lib/python3.*/site-packages" --bootloader-ignore-signals -y ssmc.py
	@echo -e "$(GREEN)✅ SSMC CLI built.$(RESET)"

build: build-ssm build-ssmc ## Build both SSM and SSMC CLIs

##@ Install

install-ssm: build-ssm ## Install SSM CLI to /usr/local/bin
	@echo -e "$(GREEN)🔗 Installing 'ssm' command...$(RESET)"
	@cp -r dist/ssm/* /usr/local/bin
	@echo -e "$(GREEN)✅ Installed as 'ssm'$(RESET)"

install-ssmc: build-ssmc ## Install SSMC CLI to /usr/local/bin
	@echo -e "$(GREEN)🔗 Installing 'ssmc' command...$(RESET)"
	@cp -r dist/ssmc/* /usr/local/bin
	@echo -e "$(GREEN)✅ Installed as 'ssmc'$(RESET)"

install: install-ssm install-ssmc ## Install both SSM and SSMC CLIs

##@ Uninstall

uninstall-ssm: ## Remove SSM CLI from /usr/local/bin
	@echo -e "$(YELLOW)🧹 Removing 'ssm' from /usr/local/bin...$(RESET)"
	@rm -f /usr/local/bin/ssm
	@rm -f /usr/local/bin/_internal
	@echo -e "$(GREEN)✅ SSM CLI uninstalled$(RESET)"

uninstall-ssmc: ## Remove SSMC CLI from /usr/local/bin
	@echo -e "$(YELLOW)🧹 Removing 'ssmc' from /usr/local/bin...$(RESET)"
	@rm -f /usr/local/bin/ssmc
	@rm -f /usr/local/bin/_internal
	@echo -e "$(GREEN)✅ SSMC CLI uninstalled$(RESET)"

uninstall: uninstall-ssm uninstall-ssmc ## Remove both SSM and SSMC CLIs

##@ Docker

run/docker: ## Run the tool inside a Docker container (Ubuntu + Python)
	@echo -e "$(GREEN)🐳 Spinning up Ubuntu container...$(RESET)"
	docker run --name ssm-app -dit -v $$(pwd):/app -w /app ubuntu:20.04 bash
	docker exec -it ssm-app apt update
	docker exec -it ssm-app apt install -y python3 python3-pip python3-venv
	docker exec -it ssm-app bash

##@ Utility

clean: ## Remove venv and Python artifacts
	@echo -e "$(YELLOW)🧼 Cleaning up...$(RESET)"
	@rm -rf venv
	@rm -rf dist/ build/
	@rm -f ssm.spec ssmc.spec
	@find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	@echo -e "$(GREEN)✅ Cleaned$(RESET)"
