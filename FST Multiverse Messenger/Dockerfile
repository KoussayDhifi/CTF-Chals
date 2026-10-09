# Dockerfile for Flask CTF Challenge - FST Multiverse Messenger
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY flag.txt .

# Remove unnecessary binaries and tools to prevent command execution
RUN rm -rf /usr/bin/wget /usr/bin/curl /bin/nc /bin/netcat /usr/bin/telnet \
    /usr/bin/gcc /usr/bin/g++ /usr/bin/make /usr/bin/perl /usr/bin/ruby \
    /bin/sh /bin/dash /bin/bash 2>/dev/null || true

# Create a non-root user
RUN useradd -m -u 1000 ctfuser && \
    chown -R ctfuser:ctfuser /app && \
    chmod 644 /app/flag.txt

# Switch to non-root user
USER ctfuser

# Expose port
EXPOSE 5000

# Run Flask application
CMD ["python", "app.py"]
