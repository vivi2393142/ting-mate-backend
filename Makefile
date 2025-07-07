.PHONY: help venv server compile sync compile-all sync-all init-db init-test-db test-db test test-keep-db cleanup-test-db

help:
	@echo "Common commands:"
	@echo "  make venv         # Show how to activate the virtual environment"
	@echo "  make server       # Start FastAPI backend server"
	@echo "  make compile      # Compile requirements.txt from requirements.in"
	@echo "  make sync         # Sync virtualenv with requirements.txt"
	@echo "  make compile-all  # Compile both requirements.txt and requirements-dev.txt"
	@echo "  make sync-all     # Sync virtualenv with both requirements.txt and requirements-dev.txt"
	@echo "  make init-db      # Initialize development database and create tables"
	@echo "  make init-test-db # Initialize test database and create tables"
	@echo "  make test-db      # Test database connection"
	@echo "  make test         # Run all tests (full flow: init-test-db -> test -> cleanup-test-db)"
	@echo "  make test-keep-db # Run tests but keep test database for inspection"
	@echo "  make cleanup-test-db # Clean up test database"

venv:
	@echo "To activate the virtual environment, run:"
	@echo "  source .venv/bin/activate"

server:
	fastapi dev app/main.py

compile:
	pip-compile requirements.in

sync:
	pip-sync requirements.txt

compile-all:
	pip-compile requirements.in
	pip-compile requirements-dev.in

sync-all:
	pip-sync requirements.txt requirements-dev.txt

init-db:
	python3 scripts/init_db.py

init-test-db:
	ENVIRONMENT=test python3 scripts/init_db.py

test-db:
	python -c "from app.core.database import test_connection; print('Database connection:', 'OK' if test_connection() else 'FAILED')"

test: init-test-db
	ENVIRONMENT=test python3 scripts/run_tests.py
	$(MAKE) cleanup-test-db

test-keep-db: init-test-db
	ENVIRONMENT=test python3 scripts/run_tests.py --keep-db

cleanup-test-db:
	ENVIRONMENT=test python3 scripts/cleanup_test_db.py