FROM python:3.6-jessie
RUN mkdir /app
WORKDIR /app
ADD requirements.txt /app
RUN pip install -U pip && pip install -r requirements.txt
ADD bot.py /app
ARG HOST
ARG TOKEN
ARG TELEGRAM_BOT_TOKEN
ENV HOST="$HOST"
ENV TOKEN="$TOKEN"
ENV TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
CMD ["python", "bot.py"]
