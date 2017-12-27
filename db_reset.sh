#!/bin/bash
echo "Removing old database"
rm -f ./app.db
echo "Removing database migration history"
rm -rf ./db_repository
echo "Creating new blank database"
./db_create.py
echo "Creating data structure"
./db_migrate.py
echo "Finished"
