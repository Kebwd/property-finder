# Railway Deployment with Node.js and Python
FROM node:18-slim

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    git \
    && apt-get clean

# Create app directory
WORKDIR /app

# Copy and install API dependencies
COPY property-finder-api/package*.json ./property-finder-api/
WORKDIR /app/property-finder-api
RUN npm ci --only=production

# Copy scraper and install Python dependencies
WORKDIR /app
COPY scraper/requirements.txt ./scraper/
RUN python3 -m pip install -r scraper/requirements.txt

# Copy all application code
COPY . .

# Create uploads directory
RUN mkdir -p /app/property-finder-api/uploads

# Set working directory back to API
WORKDIR /app/property-finder-api

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# Start the API server
CMD ["npm", "start"]
