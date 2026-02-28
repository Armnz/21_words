FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# install project dependencies via pip (including dev extras for development)
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir ".[dev]"

# copy application code
COPY . .

# expose the port used by Django
EXPOSE 8000

# default command is production gunicorn, overridden in compose for dev
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
