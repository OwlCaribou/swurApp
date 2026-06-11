FROM python:3.15.0b2-alpine3.23

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY swur.py sonarr_client.py ./

CMD ["sh", "-c", "while true; do python3 swur.py --api-key ${API_KEY} --base-url ${BASE_URL} --ignore-tag-name ${IGNORE_TAG_NAME}; sleep $((${DELAY_IN_MINUTES} * 60)); done"]
