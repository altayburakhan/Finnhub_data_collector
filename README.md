# Stock Tracker

## Overview

The Stock Tracker is a real-time stock data tracking and visualization tool. It fetches data from Finnhub.io via a WebSocket, stores it in a PostgreSQL database, and presents it through a Streamlit dashboard. This project provides users with up-to-date stock prices, key metrics, and interactive charts for informed decision-making.

## Features

-   **Real-time Data:** Fetches stock prices, volumes, and timestamps in real-time using the Finnhub WebSocket API.
-   **Data Storage:** Stores the incoming data in a PostgreSQL database for persistence and analysis.
-   **Interactive Dashboard:** Uses Streamlit to create an interactive dashboard with:
    -   Real-time price charts
    -   Key metrics (last price, average price, volume)
    -   Data tables
    -   Configurable data range
-   **Data Quality Checks:** Performs automated data quality checks to ensure data accuracy and reliability.
-   **Rate Limiting:** Implements rate limiting to prevent exceeding the Finnhub API limits.
-   **Automated Testing:** Includes a comprehensive suite of tests to ensure code quality and reliability.

## Requirements

-   Python 3.12 or higher
-   PostgreSQL 13 or higher
-   Poetry for dependency management

## Installation

1.  Install Python 3.12: Follow the instructions on the [official Python website](https://www.python.org/downloads/).
2.  Install Poetry: Follow the instructions on the [official Poetry website](https://python-poetry.org/docs/#installation).
3.  Clone this repository:

    ```bash
    git clone <repository_url>
    cd stock-tracker
    ```
4.  Install dependencies:

    ```bash
    poetry install
    ```
5.  Copy `.env.example` to `.env` and fill in your PostgreSQL and Finnhub API credentials:

    ```bash
    cp .env.example .env
    ```

    Edit the `.env` file with your actual credentials.  The following environment variables need to be set:

    ```
    POSTGRES_USER=<your_postgres_user>
    POSTGRES_PASSWORD=<your_postgres_password>
    POSTGRES_HOST=<your_postgres_host>
    POSTGRES_PORT=<your_postgres_port>
    POSTGRES_DB=<your_postgres_db>
    FINNHUB_API_KEY=<your_finnhub_api_key>
    ```
6.  Run pre-commit hooks installation:

    ```bash
    pre-commit install
    ```

## Usage

1.  **Run the data collection script:**

    ```bash
    poetry run python main.py
    ```

    This script connects to the Finnhub WebSocket and stores the incoming data in the PostgreSQL database.
2.  **Run the Streamlit dashboard:**

    ```bash
    poetry run streamlit run src/visualization/app.py
    ```

    This command starts the Streamlit application, which you can access in your browser at the displayed URL (usually `http://localhost:8501`).
3.  **Run the database reset script (if needed):**

    ```bash
    poetry run python src/database/reset_db.py
    ```

    This script resets the database by dropping the existing tables and recreating them. Use with caution as it will delete all existing data.
4.  **Run the database test connection script (if needed):**

    ```bash
    poetry run python src/database/test_connection.py
    ```

    This script tests the connection to the database and prints the PostgreSQL version and table count.
5.  **Run the data quality check script (if needed):**

    ```bash
    poetry run python src/check_data.py
    ```

    This script calculates statistics of data in the database and performs data quality checks.

## Project Structure

```
stock-tracker/
├── .github/workflows/ci.yml # CI pipeline configuration
├── .gitignore # Specifies intentionally untracked files that Git should ignore
├── .pre-commit-config.yaml # Pre-commit configuration
├── .python-version # Python version
├── README.md # Project documentation
├── mypy.ini # Mypy configuration
├── pyproject.toml # Project dependencies and build configuration
├── requirements.txt # Project dependencies (alternative to pyproject.toml)
├── setup.py # Setup file
├── src/ # Source code directory
│ ├── __init__.py # Initializes the src directory as a Python package
│ ├── check_data.py # Data quality check module
│ ├── database/ # Database related modules
│ │ ├── __init__.py # Initializes the database directory as a Python package
│ │ ├── postgres_manager.py # PostgreSQL database management module
│ │ ├── reset_db.py # Database reset module
│ │ └── test_connection.py # Database connection test module
│ ├── types/ # Type stubs
│ │ └── websocket.pyi # Websocket type stub file
│ ├── visualization/ # Visualization related modules
│ │ ├── __init__.py # Initializes the visualization directory as a Python package
│ │ └── app.py # Streamlit application for data visualization
│ └── main.py # Main application module
├── tests/ # Test suite directory
│ ├── __init__.py # Initializes the tests directory as a Python package
│ ├── conftest.py # Pytest configuration and fixtures
│ ├── test_db.py # Database tests
│ └── test_rate_limiter.py # Rate limiter tests
```

## Testing

The project includes a comprehensive test suite using `pytest`. To run the tests, use the following command:

```bash
poetry run pytest
```

## CI/CD

The project uses GitHub Actions for Continuous Integration. The CI workflow is defined in `.github/workflows/ci.yml` and includes:

-   Setting up Python 3.12
-   Installing Poetry
-   Installing dependencies
-   Running tests

## Rate Limiting

The project implements rate limiting to ensure we don't exceed Finnhub's API limits:
- WebSocket connection: Maximum 20 requests per minute
- Automatic reconnection with exponential backoff
- Rate limit error handling (HTTP 429)

## Contributing

Contributions are welcome! Please feel free to submit pull requests, report bugs, or suggest new features.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
