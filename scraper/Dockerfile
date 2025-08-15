FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y cron && \
    apt-get clean

RUN pip install PyYAML


# Copy code
COPY . /app

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create log directory
RUN mkdir -p /app/logs

COPY . .
RUN chmod +x run_scraper.sh

# Copy your cron file to the system cron directory
COPY crontab /etc/cron.d/scraper-cron

# Make sure permissions are correct
RUN chmod 0644 /etc/cron.d/scraper-cron

# Ensure cron is installed
RUN apt-get update && apt-get install -y cron

# Run cron in the foreground
CMD ["cron", "-f"]

CMD ["scrapy", "crawl", "store_spider", "-a", "config_paths=config/hk_store.yaml", "-s", "LOG_LEVEL=INFO"]
# 4) Prepare logs
RUN touch /var/log/cron.log /var/log/scraper.log \
 && chmod 0666 /var/log/cron.log /var/log/scraper.log

# 5) Launch cron in foreground
CMD ["bash","-lc","echo \"=== started $(date) ===\"; cron -f -L 8"]