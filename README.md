# Stock Tracker

## Personal Note

This is my first Python project, which I developed as my entry into the data engineering field. I chose stock market data because it provides an excellent opportunity to work with:

- Real-time streaming data (high frequency, continuous updates)
- Structured data storage and management
- Data quality monitoring and validation
- Data visualization and analytics
- ETL (Extract, Transform, Load) processes

Stock market data serves as a perfect learning ground for data engineering concepts due to its real-time nature, high volume, and structured format. This project helped me understand:

- Real-time data processing with WebSocket
- Database management with PostgreSQL
- Data visualization with Streamlit
- Modern Python development practices (type hints, testing, code quality)
- Project structuring and modular design
- Version control with Git and pre-commit hooks

Through this project, I've gained practical experience in building a complete data pipeline, from data collection to storage and visualization, which are fundamental skills in data engineering.

## Overview

The Stock Tracker is a real-time stock data tracking and visualization tool. It fetches data from Finnhub.io via a WebSocket, stores it in a PostgreSQL database, and presents it through a Streamlit dashboard. This project provides users with up-to-date stock prices, key metrics, and interactive charts for informed decision-making.

## Features

Hi! Here are the main features I've developed in this project:

-   **Real-time Data Collection:** I collect real-time stock prices using Finnhub's WebSocket API. The `FinnhubWebSocket` class in `main.py` handles this process. Working with WebSocket was a new experience for me and quite educational.

-   **Data Storage:** I store all the collected data in a PostgreSQL database. The `PostgresManager` class in `src/database/postgres_manager.py` manages database operations. I'm continuously improving my SQL and database management skills.

-   **Dashboard:** I developed a dashboard using Streamlit. It includes:
    -   Real-time price charts (using Plotly)
    -   Key metrics (latest price, average price, trading volume)
    -   Data tables
    -   Customizable time range
    You can find all the dashboard code in `src/visualization/app.py`.

-   **Data Quality Checks:** I perform various analyses using `check_data.py` to verify data accuracy. This allows me to continuously monitor data quality.

-   **Rate Limiting:** I developed a `RateLimiter` class in `src/utils/rate_limiter.py` to manage Finnhub API limits. Optimizing API usage has been an important learning experience.

-   **Tests:** I added a test suite to ensure code reliability. You can find the tests in the `tests` directory. I'm continuously improving my testing skills.

-   **CI/CD:** I set up an automated testing system using GitHub Actions. Tests run automatically with each code update. Learning CI/CD processes has been a valuable experience.

Note: This project marks the beginning of my data engineering journey. I'll continue to expand and improve it as I learn and grow.

## Requirements

-   Python 3.12 or higher
-   PostgreSQL 13 or higher
-   Poetry for dependency management
-   Dependencies listed in `pyproject.toml` (or `requirements.txt`):
    -   `websocket-client`: For WebSocket communication with Finnhub.
    -   `python-dotenv`: For loading environment variables from a `.env` file.
    -   `SQLAlchemy`: For interacting with the PostgreSQL database.
    -   `psycopg2-binary`: PostgreSQL adapter for Python.
    -   `streamlit`: For creating the interactive dashboard.
    -   `plotly`: For creating interactive charts in Streamlit.
    -   `pandas`: For data manipulation and analysis.

## Installation

1.  Install Python 3.12: Follow the instructions on the [official Python website](https://www.python.org/downloads/).
2.  Install Poetry: Follow the instructions on the [official Poetry website](https://python-poetry.org/docs/#installation).
3.  Clone this repository:

    ```bash
    git clone https://github.com/altayburakhan/Finnhub_data_collector.git
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

    Edit the `.env` file with your actual credentials. The following environment variables need to be set:

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
├── .github/
│   └── workflows/
│       └── ci.yml              # CI pipeline configuration
├── .gitignore                  # Git ignore rules
├── .pre-commit-config.yaml     # Pre-commit hook configuration
├── .python-version             # Python version specification
├── README.md                   # Project documentation
├── mypy.ini                    # Mypy configuration
├── pyproject.toml              # Poetry configuration and dependencies
├── requirements.txt            # Alternative dependency specification
├── setup.py                    # Setup configuration
├── src/                        # Source code directory
│   ├── __init__.py            # Package initialization
│   ├── check_data.py          # Data quality check module
│   ├── database/              # Database related modules
│   │   ├── __init__.py        # Package initialization
│   │   ├── postgres_manager.py # PostgreSQL management
│   │   ├── reset_db.py        # Database reset utility
│   │   └── test_connection.py # Connection testing
│   ├── types/                 # Type stub files
│   │   └── websocket.pyi      # WebSocket type definitions
│   ├── utils/                 # Utility modules
│   │   ├── __init__.py        # Package initialization
│   │   └── rate_limiter.py    # Rate limiting implementation
│   ├── visualization/         # Visualization modules
│   │   ├── __init__.py        # Package initialization
│   │   └── app.py             # Streamlit dashboard
│   └── main.py                # Main application entry point
└── tests/                     # Test suite directory
    ├── __init__.py            # Test package initialization
    ├── conftest.py            # Test configuration and fixtures
    ├── test_db.py             # Database tests
    └── test_rate_limiter.py   # Rate limiter tests
```

## Testing

The project includes a comprehensive test suite using `pytest`. The test configuration and fixtures are defined in `tests/conftest.py` (startLine: 20, endLine: 173). To run the tests, use the following command:

```bash
poetry run pytest
```

## CI/CD

The project uses GitHub Actions for Continuous Integration. The CI workflow is defined in `.github/workflows/ci.yml` and includes:

-   Setting up Python ${{ matrix.python-version }}
-   Installing Poetry
-   Installing dependencies
-   Running tests

