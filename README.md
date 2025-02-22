# Stock Tracker

## Personal Note

This is my first Python project as I begin my journey into data engineering. I chose to work with stock market data because it provides great learning opportunities with:

- Real-time data streaming
- Data storage and management
- Data quality monitoring
- Visualization and analytics
- Basic ETL processes

Through this project, I've learned valuable skills:
- Working with WebSocket for real-time data
- Setting up and managing a PostgreSQL database
- Building interactive dashboards with Streamlit
- Writing better Python code with type hints
- Project organization and Git workflow

## What It Does

This is a real-time stock tracking application that:
1. Collects live stock prices from Finnhub.io
2. Stores the data in PostgreSQL
3. Visualizes it through an interactive dashboard

## Features

Here are the main components I've built:

-   **Real-time Data Collection:** Using Finnhub's WebSocket API to collect live stock prices. The `FinnhubWebSocket` class in `main.py` handles the connection and data processing. This was my first experience with WebSocket technology.

-   **Data Storage:** All data is stored in a PostgreSQL database. The `PostgresManager` class in `src/database/postgres_manager.py` manages the database operations. I'm learning more about SQL and database management as I go.

-   **Dashboard:** Built using Streamlit, featuring:
    -   Real-time price charts with Plotly
    -   Key metrics (latest price, average price, volume)
    -   Interactive data tables
    -   Customizable time ranges
    The dashboard code is in `src/visualization/app.py`.

-   **Data Quality Checks:** Implemented various checks in `check_data.py` to ensure data accuracy and consistency.

-   **Rate Limiting:** Created a `RateLimiter` class in `src/utils/rate_limiter.py` to manage API request limits effectively.

-   **Tests:** Added a basic test suite to catch potential issues early. The tests are in the `tests` directory.

-   **CI/CD:** Set up GitHub Actions for automated testing on code updates.

Note: As my first data engineering project, I'm continuously learning and looking to improve it further.

## Requirements

-   Python 3.12+
-   PostgreSQL 13+
-   Poetry for dependency management
-   Main dependencies:
    -   `websocket-client`: WebSocket communication
    -   `python-dotenv`: Environment variable management
    -   `SQLAlchemy`: Database ORM
    -   `psycopg2-binary`: PostgreSQL adapter
    -   `streamlit`: Dashboard creation
    -   `plotly`: Data visualization
    -   `pandas`: Data manipulation

## Installation

1.  Install Python 3.12 from the [official Python website](https://www.python.org/downloads/)
2.  Install Poetry from the [official Poetry website](https://python-poetry.org/docs/#installation)
3.  Clone this repository:
    ```bash
    git clone https://github.com/altayburakhan/Finnhub_data_collector.git
    cd stock-tracker
    ```

4.  Install dependencies:
    ```bash
    poetry install
    ```

5.  Set up environment variables:
    ```bash
    cp .env.example .env
    ```
    Configure your `.env` file:
    ```
    POSTGRES_USER=your_username
    POSTGRES_PASSWORD=your_password
    POSTGRES_HOST=localhost
    POSTGRES_PORT=5432
    POSTGRES_DB=stockdb
    FINNHUB_API_KEY=your_api_key
    ```

6.  Install pre-commit hooks:
    ```bash
    pre-commit install
    ```

## Usage

1.  Start data collection:
    ```bash
    poetry run python main.py
    ```

2.  Launch the dashboard:
    ```bash
    poetry run streamlit run src/visualization/app.py
    ```
    Access it at `http://localhost:8501`

3.  Database management:
    ```bash
    # Reset database (caution: deletes existing data)
    poetry run python src/database/reset_db.py

    # Test database connection
    poetry run python src/database/test_connection.py

    # Check data quality
    poetry run python src/check_data.py
    ```

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

Run tests with:
```bash
poetry run pytest
```

## Future Improvements

Areas I plan to work on:
- Expand stock coverage
- Enhance dashboard functionality
- Improve error handling
- Add more comprehensive tests
- Optimize data storage

Feedback and suggestions are welcome as I continue to learn and improve this project.
