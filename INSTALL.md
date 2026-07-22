# Installation

## 1. Prerequisites

- **Python 3.11 or later** – download from [python.org](https://www.python.org/)
- **pip** (comes with Python)
- A Unix‑like shell (Linux, macOS) or Windows terminal

## 2. Get the code

Clone the repository and enter the project directory:

```bash
git clone <repository-url>
cd warehouse-inventory-manager
```

## 3. Set up a virtual environment and install dependencies

```bash
# Create and activate a virtual environment (Unix)
python -m venv .venv && . .venv/bin/activate

# On Windows, use: python -m venv .venv && venv\Scripts\activate

# Install the required packages
pip install -r requirements.txt
```

## 4. Configure environment variables

Copy the example environment file and edit it with your values:

```bash
cp .env.example .env
```

Set at least:
- `ADMIN_PASSWORD` – for the seed administrator account
- `DEMO_PASSWORD` – for the seed demo account
- `SECRET_KEY` – a random string (use `openssl rand -hex 32`)
- `DATABASE_URL` – leave as `sqlite:///./app.db` to use the file‑based SQLite database

## 5. Database

The application uses SQLite and creates the database file (`app.db`) automatically on first startup. Seed data (users, products, categories) is also inserted at that time. No manual migration commands are required.

## 6. Run the development server

```bash
uvicorn app.main:app --reload
```

The server starts at `http://127.0.0.1:8000` by default.

## 7. Tests

No test suite is included in this release.

## 8. Production build

No separate build step is configured. For production, run Uvicorn without `--reload` and behind a reverse proxy.

## 9. Troubleshooting

- **Port already in use**: Change the port with `--port 8080`.
- **ModuleNotFoundError**: Ensure you are in the project root and the virtual environment is activated.
- **Missing .env**: Verify `.env` exists and contains all required variables.
- **Activation fails on Windows**: Use `venv\Scripts\activate` instead of the dot command.
- **SQLite errors**: Check that the directory is writable and `DATABASE_URL` is correctly set.