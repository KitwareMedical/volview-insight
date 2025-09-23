FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

WORKDIR /app

# Copy Poetry files
COPY pyproject.toml poetry.lock ./

# Configure Poetry
RUN poetry config virtualenvs.create false

# Install dependencies (only production dependencies, skip current project)
RUN poetry install --only=main --no-root

# Copy application code
COPY . .

# Expose port
EXPOSE 4014

# Run the application
CMD ["python", "-m", "volview_server", "-P", "4014", "-H", "0.0.0.0", "volview_insight_methods.py"]