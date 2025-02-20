FROM python:3.12-slim

WORKDIR /app

# Poetry kurulumu
RUN pip install poetry

# Bağımlılıkları kopyala ve kur
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Uygulama kodunu kopyala
COPY . .

# Uygulamayı çalıştır
CMD ["poetry", "run", "python", "main.py"]
