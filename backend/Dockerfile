FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./

# Install build tools (needed only if a package must be built from source)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential cargo gcc libpq-dev git \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV PORT=8000

EXPOSE 8000

CMD ["bash", "-lc", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
