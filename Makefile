install:
	@echo "Installing ssm..."
	chmod +x ssm.py
	ln -sf $(PWD)/ssm.py /usr/local/bin/ssm
	@echo "Done. You can now run 'ssm' from anywhere."

uninstall:
	@echo "Uninstalling ssm..."
	rm -f /usr/local/bin/ssm
	@echo "Removed 'ssm' binary."
