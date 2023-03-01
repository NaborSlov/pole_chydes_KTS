#!/usr/bin/env bash

export ALEMBIC_URL="sqlalchemy_test."
cd "$PYTHONPATH" || exit
alembic upgrade head
