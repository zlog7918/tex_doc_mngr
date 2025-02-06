FROM python:3.12.7-alpine3.20
ARG APP_MAIN_DIR
ARG DOC_FILES_DIR
ARG TEMP_FOLDER

RUN adduser -DHs /sbin/nologin py_flask

ENV APP_VENV_DIR=/opt/venv
ENV APP_MAIN_DIR=${APP_MAIN_DIR}
ENV APP_DIR=${APP_MAIN_DIR}/app

RUN apk add --no-cache build-base linux-headers pcre-dev libpq-dev


RUN apk add --no-cache texlive-full

RUN apk add --no-cache python3 py3-pygments

RUN mkdir -p ${DOC_FILES_DIR}/tmp && \
    chown -R py_flask:py_flask ${DOC_FILES_DIR}/tmp && \
    chmod -R 777 ${DOC_FILES_DIR}/tmp

RUN mkdir -p ${TEMP_FOLDER} && \
    chown -R py_flask:py_flask ${TEMP_FOLDER} && \
    chmod -R 777 ${TEMP_FOLDER}


COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uwsgi", "--ini", "/var/www/nginx/app.ini"]


WORKDIR ${APP_DIR}
COPY ./requirements.txt ${APP_MAIN_DIR}/
RUN python3 -m venv ${APP_VENV_DIR} && . ${APP_VENV_DIR}/bin/activate && python3 -m pip --no-cache-dir install -r ${APP_MAIN_DIR}/requirements.txt

COPY ./app.ini ${APP_MAIN_DIR}/
CMD ["sh", "-c", "\"${APP_VENV_DIR}/bin/uwsgi\" --uid py_flask --ini \"${APP_MAIN_DIR}/app.ini\" --virtualenv \"${APP_VENV_DIR}/\""]
