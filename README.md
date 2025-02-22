# Stock Tracker 📈

## Hey there! 👋

This is my very first Python project, and I'm super excited to share it! I've just started my journey into data engineering, and I wanted to create something that would help me learn the fundamentals. I chose to work with stock market data because, well, who doesn't love watching those numbers go up and down in real-time? 😄

What made me choose stock data? Here's why:
- It's real-time (things happen super fast!)
- There's lots of data to play with
- I get to learn how to store and manage data properly
- I can make cool visualizations
- It feels like a real-world project

Through this project, I've learned so many cool things:
- How to work with WebSocket (it's like magic - data just flows in!)
- Setting up my first real database with PostgreSQL
- Creating a dashboard that actually looks good (thanks Streamlit!)
- Writing proper Python code (type hints are your friends!)
- How to structure a project (folders everywhere!)
- Using Git without messing everything up 😅

## What Does This Thing Do?

Simply put, it's a real-time stock tracker! It:
1. Grabs live stock prices from Finnhub.io
2. Stores them in a database (PostgreSQL)
3. Shows everything in a nice dashboard

## Features

Hi! Here are the cool things I managed to build:

-   **Real-time Data Collection:** I'm grabbing live stock prices using Finnhub's WebSocket API! The `FinnhubWebSocket` class in `main.py` does all the heavy lifting. I had never worked with WebSockets before, so this was pretty exciting to figure out.

-   **Data Storage:** Everything goes into a PostgreSQL database (my first time setting up a real database!). The `PostgresManager` class in `src/database/postgres_manager.py` handles all the database stuff. I'm still learning SQL, but it's getting better every day!

-   **Dashboard:** I built this using Streamlit (which is amazing by the way!). Check out what it can do:
    -   Live price charts that update automatically (Plotly makes them look professional!)
    -   Important numbers like latest price and trading volume
    -   Data tables that you can sort and filter
    -   You can choose different time ranges to look at
    You can find all this in `src/visualization/app.py` if you're curious!

-   **Data Quality Checks:** I added some checks in `check_data.py` to make sure the data makes sense. Nothing worse than garbage data, right?

-   **Rate Limiting:** Had to build a `RateLimiter` class in `src/utils/rate_limiter.py` because apparently, you can't just hammer an API with requests 😅. Learned that the hard way!

-   **Tests:** Yes, I wrote tests! They're not perfect, but they're helping me catch bugs before they become problems. You can find them in the `tests` directory.

-   **CI/CD:** I even set up GitHub Actions! It automatically runs all the tests whenever I push new code. Feels pretty professional, not gonna lie!

Note: This is just the beginning of my data engineering adventure! I know there's so much more to learn and improve, but hey, you gotta start somewhere, right? 🚀

## Want to Try It Out?

You'll need:
-   Python 3.12 or newer
-   PostgreSQL 13 or newer
-   Poetry (it's like pip but fancier!)

Here are the main packages I'm using (they're all in `pyproject.toml`):
-   `websocket-client`: For getting that sweet real-time data
-   `python-dotenv`: For keeping my secrets secret
-   `SQLAlchemy`: Makes talking to the database way easier
-   `psycopg2-binary`: PostgreSQL's best friend
-   `streamlit`: For that awesome dashboard
-   `plotly`: Makes the charts look good
-   `pandas`: Because everyone uses pandas!

## Installation

1.  First, grab Python 3.12 from the [Python website](https://www.python.org/downloads/)
2.  Install Poetry - trust me, it makes life easier! [Get it here](https://python-poetry.org/docs/#installation)
3.  Clone this repo:
    ```bash
    git clone https://github.com/altayburakhan/Finnhub_data_collector.git
    cd stock-tracker
    ```

4.  Install all the packages:
    ```bash
    poetry install
    ```

5.  Create a `.env` file for your secrets:
    ```bash
    cp .env.example .env
    ```
    Then fill in your details:
    ```
    POSTGRES_USER=your_username
    POSTGRES_PASSWORD=your_password
    POSTGRES_HOST=localhost
    POSTGRES_PORT=5432
    POSTGRES_DB=stockdb
    FINNHUB_API_KEY=your_api_key
    ```

6.  Set up pre-commit hooks (catches silly mistakes before they happen!):
    ```bash
    pre-commit install
    ```

## Running the Project

1.  Start collecting data:
    ```bash
    poetry run python main.py
    ```
    This starts grabbing live stock data!

2.  Fire up the dashboard:
    ```bash
    poetry run streamlit run src/visualization/app.py
    ```
    Then open your browser and go to `http://localhost:8501` - pretty cool, right?

3.  Need to reset the database?
    ```bash
    poetry run python src/database/reset_db.py
    ```
    ⚠️ Warning: This deletes everything! Use with care!

4.  Want to check if everything's connected properly?
    ```bash
    poetry run python src/database/test_connection.py
    ```

5.  Check data quality:
    ```bash
    poetry run python src/check_data.py
    ```

## Project Structure

I tried to keep things organized (it's harder than it looks!):

```
stock-tracker/
├── src/                        # Where all the magic happens
│   ├── database/              # Database stuff
│   ├── utils/                 # Helper functions
│   ├── visualization/         # Dashboard code
│   └── main.py               # The main script
└── tests/                     # Making sure things work
```

## Testing

Run the tests with:
```bash
poetry run pytest
```
(Watching the tests pass is surprisingly satisfying!)

## What's Next?

I've got a bunch of ideas for improvements:
- Add more stocks to track
- Make the dashboard even prettier
- Add some machine learning stuff maybe?
- Improve error handling
- Write more tests

Feel free to try it out, and let me know what you think! This is my first real project, so any feedback is super welcome! 😊

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
