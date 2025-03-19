#!/bin/sh

SUBJ_TXT='/C=PL/ST=Mazowieckie/L=Warsaw/O=TDM Sp. z o.o./OU=IT Department/CN=doc-mngr.pl'
CERT_NAME=cert

func_start() {
    if func_if_exists
    then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$CERT_DIR/$CERT_NAME.key" \
            -out "$CERT_DIR/$CERT_NAME.crt" \
            -subj "$SUBJ_TXT"
        # openssl req -new -key "$CERT_DIR/$CERT_NAME.key" -out "$CERT_DIR/$CERT_NAME.csr" -subj "$SUBJ_TXT"
    fi
}

func_if_exists() {
    [ ! -e "$CERT_DIR/$CERT_NAME.crt" ] && return 0
    [ ! -e "$CERT_DIR/$CERT_NAME.key" ] && return 0
    # [ ! -e "$CERT_DIR/$CERT_NAME.csr" ] && return 0
    return 1
}

func_start
sh /docker-entrypoint.sh nginx -g 'daemon off;'