FROM nginx:1.27.2-alpine3.20-slim

RUN apk add --no-cache openssl

COPY ./start.sh /var/start_sh/
ENTRYPOINT ["/bin/sh", "/var/start_sh/start.sh"]
