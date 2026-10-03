FROM python:3.14.7-alpine3.23

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY swur.py sonarr_client.py ./
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
CMD ["sh", "-c", "interval=${CHECK_INTERVAL:-${DELAY_IN_MINUTES:-60}}; if ! [ \"$interval\" -gt 0 ] 2>/dev/null; then echo \"CHECK_INTERVAL must be a positive whole number of minutes, got '$interval'\" >&2; exit 2; fi; while true; do python3 swur.py --api-key ${API_KEY} --base-url ${BASE_URL} --ignore-tag-name ${IGNORE_TAG_NAME:-ignore} --wait-until-end ${WAIT_UNTIL_END:-True} --extra-delay ${EXTRA_DELAY:-0}; [ $? -ne 2 ] || exit 2; sleep $((interval * 60)); done"]
