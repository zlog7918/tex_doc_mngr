FROM python:3.12.7-alpine3.20
ARG APP_MAIN_DIR
RUN adduser -DHs /sbin/nologin py_flask

ENV APP_VENV_DIR=/opt/venv
ENV APP_MAIN_DIR=${APP_MAIN_DIR}
ENV APP_DIR=${APP_MAIN_DIR}/app

RUN apk add --no-cache build-base linux-headers pcre-dev libpq-dev

WORKDIR ${APP_DIR}
COPY ./requierments.txt ${APP_MAIN_DIR}/
RUN python3 -m venv ${APP_VENV_DIR} && . ${APP_VENV_DIR}/bin/activate && python3 -m pip --no-cache-dir install -r ${APP_MAIN_DIR}/requierments.txt

COPY ./app.ini ${APP_MAIN_DIR}/
CMD ["sh", "-c", "\"${APP_VENV_DIR}/bin/uwsgi\" --uid py_flask --ini \"${APP_MAIN_DIR}/app.ini\" --virtualenv \"${APP_VENV_DIR}/\""]
