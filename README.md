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

## Dashboard Preview

![Stock Tracker Dashboard](https://i.imgur.com/JQZPrWu.png)


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
    cd Finnhub_data_collector
    ```

4.  Install dependencies:
    ```bash
    poetry install
    poetry shell  # Activate the virtual environment
    ```

5.  Set up environment variables:
    ```bash
    cp .env.example .env
    ```
    Configure your `.env` file with your database credentials and Finnhub API key:
    ```
    FINNHUB_API_KEY=your_api_key_here
    
    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=postgres
    DB_USER=postgres
    DB_PASSWORD=your_password_here
    
    POSTGRES_HOST=localhost
    POSTGRES_PORT=5432
    POSTGRES_DB=postgres
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=your_password_here
    ```

6.  Install pre-commit hooks (optional):
    ```bash
    pre-commit install
    ```

## Usage

1.  Start data collection:
    ```bash
    python main.py
    ```

2.  Launch the dashboard:
    ```bash
    streamlit run src/visualization/app.py
    ```
    Access it at `http://localhost:8501`

3.  Database management:
    ```bash
    # Reset database (caution: deletes existing data)
    python src/database/reset_db.py

    # Test database connection
    python src/database/test_connection.py

    # Check data quality
    python src/check_data.py
    ```

## Project Structure

```
Finnhub_data_collector/
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
├── main.py                     # Main application entry point
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
└── tests/                     # Test suite directory
    ├── __init__.py            # Test package initialization
    ├── conftest.py            # Test configuration and fixtures
    ├── test_db.py             # Database tests
    └── test_rate_limiter.py   # Rate limiter tests
```

## Testing

Run tests with:
```bash
pytest
```

## Future Improvements

Areas I plan to work on:
- Expand stock coverage
- Enhance dashboard functionality
- Improve error handling
- Add more comprehensive tests
- Optimize data storage

Feedback and suggestions are welcome as I continue to learn and improve this project.
