#! /bin/bash

until celery -A invenio_app worker
do
  echo "Celery failed, retry in 5s"
  sleep 5
done
