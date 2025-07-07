# TingMate Backend

## Project Overview

**TingMate** is a daily support app designed for memory-impaired individuals and their caregivers, featuring an AI voice assistant to help manage reminders and tasks. The backend provides the API, business logic, and data management for the TingMate ecosystem.

This repository contains the backend implementation, built with Python and FastAPI.

## Project Structure

- `app/`: Main application code
  - `api/`: API route definitions
  - `core/`: Core settings, configuration, and utilities
  - `db/`: Database-related modules
  - `repositories/`: Data access layer (SQL operations, e.g. user.py, task.py)
  - `schemas/`: Data schemas
  - `services/`: Business logic and service layer
  - `main.py`: Application entry point
- `tests/`: Test cases and testing utilities
- `requirements.txt`: Python dependencies
- `.venv/`: Virtual environment (not included in version control)

## Getting Started

### 1. Create and Activate Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

If you use pip-tools:

```bash
pip install pip-tools
pip-compile requirements.in
pip-compile requirements-dev.in  # For development dependencies (optional)
pip-sync requirements.txt requirements-dev.txt
```

Or, if you just want to install from requirements.txt:

```bash
pip install -r requirements.txt
```

### 3. Run the FastAPI Server

```bash
fastapi dev app/main.py
```

---

- Make sure to activate your virtual environment before running any commands.
- Update dependencies with `pip-compile` whenever you change `requirements.in` or `requirements-dev.in`.
- Use `pip-sync` to keep your environment in sync with the requirements files.

## Get started

<!-- TODO: Add section -->
