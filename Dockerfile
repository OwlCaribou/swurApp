FROM python:3.13.5-alpine3.22

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY swur.py sonarr_client.py .

CMD ["sh", "-c", "while true; do python3 swur.py --api-key ${API_KEY} --base-url ${BASE_URL}; sleep ${DELAY}; done"]
