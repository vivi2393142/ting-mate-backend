# TingMate Backend

## Project Overview

**TingMate** is a daily support app designed for memory-impaired individuals and their caregivers, featuring an AI voice assistant to help manage reminders and tasks. The backend provides the API, business logic, and data management for the TingMate ecosystem.

This repository contains the backend implementation, built with Python and FastAPI.

## Technologies & External Services

- **FastAPI**: Web framework for building APIs
- **Gemini (Google GenAI)**: Used for LLM (Large Language Model) features
- **AssemblyAI Speech-to-Text**: For audio transcription (voice to text)
- **MySQL**: Main database
- **Pydantic**: Data validation and settings
- **Other common Python libraries**

## Project Structure

- `app/`: Main application code
  - `api/`: API route definitions (REST endpoints)
  - `core/`: Core settings, configuration, and utilities
  - `db/`: Database initialization and connection
  - `repositories/`: Data access layer (SQL operations, CRUD logic)
  - `schemas/`: Data schemas (Pydantic models for validation)
  - `services/`: Business logic and service layer (LLM, speech, user, etc.)
  - `main.py`: Application entry point
- `scripts/`: Helper scripts for development and deployment
- `requirements.in`: Main dependency list (for pip-tools)
- `requirements.txt`: Locked dependencies (production)
- `requirements-dev.in`: Dev/test dependency list (for pip-tools)
- `requirements-dev.txt`: Locked dev dependencies
- `pytest.ini`: Pytest configuration
- `Makefile`: Common development commands
- `tests/`: Test cases and testing utilities
- `.venv/`: Virtual environment (not included in version control)

## Environment Variables

The following environment variables are required to run the project:

- `ASSEMBLYAI_API_KEY` — AssemblyAI API key for speech-to-text
- `GEMINI_API_KEY` — Gemini (Google GenAI) API key for LLM features
- `GEMINI_MODEL_NAME` — Gemini model name for LLM features (e.g., "gemini-2.5-flash")
- `DB_HOST` — MySQL database host
- `DB_USER` — MySQL database user
- `DB_PASSWORD` — MySQL database password
- `DB_NAME` — MySQL database name

You can set these in a `.env` file in the project root.

## Getting Started

### 1. Create and Activate a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

To install all dependencies (including development and testing), use the Makefile:

```bash
make sync-all  # Installs both production and development dependencies
```

Or, to install only production dependencies:

```bash
make sync  # Installs only production dependencies
```

### 3. Initialize the Database

To initialize or migrate the database, use the provided Makefile command:

```bash
make init-db
```

### 4. Run the FastAPI Server

```bash
make server
```

### 5. Run Tests

To run all tests:

```bash
make test
```

Or you can use pytest directly:

```bash
pytest
```
