FROM python:3.12.7-alpine3.20
ARG APP_MAIN_DIR

ENV APP_VENV_DIR=/opt/venv
ENV APP_MAIN_DIR=${APP_MAIN_DIR}
ENV APP_DIR=${APP_MAIN_DIR}/app


WORKDIR ${APP_DIR}
COPY ./requirements.txt ${APP_MAIN_DIR}/
RUN python3 -m venv ${APP_VENV_DIR} && . ${APP_VENV_DIR}/bin/activate && python3 -m pip --no-cache-dir install -r ${APP_MAIN_DIR}/requirements.txt

COPY ./test_src ${APP_DIR}/

CMD ["sh", "-c", ". ${APP_VENV_DIR}/bin/activate && python3 ${APP_DIR}/testapp.py"]
