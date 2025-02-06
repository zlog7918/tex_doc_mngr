#!/bin/sh
echo "Ustawianie uprawnień dla ${DOC_FILES_DIR} i ${TEMP_FOLDER}..."
mkdir -p "${DOC_FILES_DIR}" "${TEMP_FOLDER}"
chown -R py_flask:py_flask "${DOC_FILES_DIR}" "${TEMP_FOLDER}"
chmod -R 750 "${DOC_FILES_DIR}" "${TEMP_FOLDER}"

# Uruchom aplikację
exec "$@"
