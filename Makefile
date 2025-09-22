.PHONY: venv
venv:
	@echo "Creating virtual environment..."
	python3 -m venv .venv
	@echo "Virtual environment created."

.PHONY: install
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "Dependencies installed."

.PHONY: test
test:
	@echo "Running tests..."
	cd client && python mcp_client.py && cd ..
	@echo "Tests completed."

.PHONY: app
app:
	@echo "Starting the application..."
	streamlit run streamlit_app.py
	@echo "Application started."