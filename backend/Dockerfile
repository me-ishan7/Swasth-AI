## Dockerfile for SwasthAI Python Backend (Flask API)
FROM python:3.11-slim

# Install curl for healthchecks
RUN apt-get update \
	&& apt-get install -y --no-install-recommends curl \
	&& rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
	&& pip cache purge

# Copy all backend source (models, utils, app.py, etc.)
COPY . .

# Expose port
EXPOSE 5000

# Environment
ENV FLASK_ENV=production

# Run the application
CMD ["python", "app.py"]
