from setuptools import setup, find_packages

setup(
    name="finnhub_data_collector",
    packages=find_packages(),
    install_requires=[
        "websocket-client",
        "python-dotenv",
        "SQLAlchemy",
        "psycopg2-binary",
        "streamlit",
        "plotly",
        "pandas",
    ],
)