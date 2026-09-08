FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY backend/ backend/
COPY data/ data/
COPY starter-datasets/ starter-datasets/

# Create upload directory
RUN mkdir -p data/uploads

# Set working directory to backend
WORKDIR /app/backend

# Expose port
EXPOSE 8000

# Run the server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
