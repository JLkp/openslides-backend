#!/bin/bash

export DATASTORE_DATABASE_HOST=${DATASTORE_DATABASE_HOST:-postgresql}
export DATASTORE_DATABASE_PORT=${DATASTORE_DATABASE_PORT:-5432}
export DATASTORE_DATABASE_USER=${DATASTORE_DATABASE_USER:-openslides}
export DATASTORE_DATABASE_NAME=${DATASTORE_DATABASE_NAME:-openslides}
export DATASTORE_DATABASE_PASSWORD_FILE=${DATASTORE_DATABASE_PASSWORD_FILE:-/run/secrets/postgres_password}
case $OPENSLIDES_DEVELOPMENT in
    1|on|On|ON|true|True|TRUE)  export PGPASSWORD="openslides";;
    *)                          export PGPASSWORD="$(cat "$DATASTORE_DATABASE_PASSWORD_FILE")";;
esac