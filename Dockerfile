# Dockerfile (known-good for HF docker sdk)
FROM python:3.11-slim

WORKDIR /home/user/app

# Deps
COPY requirements.txt /home/user/app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# App
COPY . /home/user/app

# Make imports predictable
ENV PYTHONPATH=/home/user/app
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV PORT=8501

EXPOSE 8501

# Run the app
CMD ["streamlit", "run", "projects/ai-travel-planner/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]