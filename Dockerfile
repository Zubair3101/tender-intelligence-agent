FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models FASTEMBED_CACHE_PATH=/models

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY tender_agent ./tender_agent
COPY ui ./ui
COPY scripts ./scripts
COPY data/company_profile.yaml ./data/company_profile.yaml

EXPOSE 8000 8501
CMD ["uvicorn", "tender_agent.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
