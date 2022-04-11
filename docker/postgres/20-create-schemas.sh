#!/usr/bin/env bash
set -e

# TODO для корректного создания схем в Postgres прописать свой вариант
export VARIANT=v2
export SCRIPT_PATH=/docker-entrypoint-initdb.d/
export PGPASSWORD=test
psql -U program -d services -f "$SCRIPT_PATH/schemes/schema-$VARIANT.sql"
#psql -U program -d services -f "$SCRIPT_PATH/schemes/test_data.sql"
#psql -U postgres -d services -f ./docker-entrypoint-initdb.d/schemes/test_data.sql