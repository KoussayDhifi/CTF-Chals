FROM python:3.11-slim

WORKDIR /FST-Prime-Secure_Portal

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application (including flag.txt)
COPY . .

EXPOSE 5000

CMD ["python", "challenge/app.py"]