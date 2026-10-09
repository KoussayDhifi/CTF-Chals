FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

# --- System deps for Playwright ---
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    libdrm2 \
    libxshmfence1 \
    libxfixes3 \
    libxext6 \
    libx11-6 \
    libxrender1 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# --- Workdir ---
WORKDIR /app

# --- Install Python deps ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Install Playwright browser ---
RUN playwright install chromium

# --- Copy full challenge ---
COPY . .

# --- Expose Flask ---
EXPOSE 5000

# --- Ensure flag exists (infra override allowed) ---
RUN test -f flag.txt || echo "Securinets_fst{Konstantiniyyeh_shall_be_conquered}" > flag.txt

# --- Start Flask + admin bot ---
CMD python challenge/app.py & python adminbot/bot.py
