# Dockerfile
FROM python:3.10-slim

# System deps for Playwright
RUN apt-get update && apt-get install -y \
    libnspr4 libnss3 libatk1.0-0 libatk-bridge2.0-0 libatspi2.0-0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libxkbcommon0 libasound2 curl wget gnupg && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Install Playwright + Browsers
RUN playwright install --with-deps

EXPOSE 7860

CMD ["streamlit", "run", "audit_app.py", "--server.port=7860", "--server.address=0.0.0.0"]
