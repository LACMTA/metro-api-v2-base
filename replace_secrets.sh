#!/bin/bash

# Read the secrets from the environment variables
FTP_SERVER=$FTP_SERVER
FTP_USERNAME=$FTP_USERNAME
FTP_PASS=$FTP_PASS
SWIFTLY_AUTH_KEY_BUS=$SWIFTLY_AUTH_KEY_BUS
SWIFTLY_AUTH_KEY_RAIL=$SWIFTLY_AUTH_KEY_RAIL
AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
ACCESS_SECRET_KEY=$ACCESS_SECRET_KEY
SWIFTLY_AUTH_KEY=$SWIFTLY_AUTH_KEY
API_DB_URI=$API_DB_URI
HASH_KEY=$HASH_KEY
HASHING_ALGORITHM=$HASHING_ALGORITHM
LOGZIO_TOKEN=$LOGZIO_TOKEN

# Use sed to replace the placeholders in the JSON file
sed -i "s/\${{secrets.FTP_SERVER}}/$FTP_SERVER/g" params-api.json
sed -i "s/\${{secrets.FTP_USERNAME}}/$FTP_USERNAME/g" params-api.json
sed -i "s/\${{secrets.FTP_PASS}}/$FTP_PASS/g" params-api.json
sed -i "s/\${{secrets.SWIFTLY_AUTH_KEY_BUS}}/$SWIFTLY_AUTH_KEY_BUS/g" params-api.json
sed -i "s/\${{secrets.SWIFTLY_AUTH_KEY_RAIL}}/$SWIFTLY_AUTH_KEY_RAIL/g" params-api.json
sed -i "s/\${{secrets.AWS_ACCESS_KEY_ID}}/$AWS_ACCESS_KEY_ID/g" params-api.json
sed -i "s/\${{secrets.ACCESS_SECRET_KEY}}/$ACCESS_SECRET_KEY/g" params-api.json
sed -i "s/\${{secrets.SWIFTLY_AUTH_KEY}}/$SWIFTLY_AUTH_KEY/g" params-api.json
sed -i "s/\${{secrets.API_DB_URI}}/$API_DB_URI/g" params-api.json
sed -i "s/\${{secrets.HASH_KEY}}/$HASH_KEY/g" params-api.json
sed -i "s/\${{secrets.HASHING_ALGORITHM}}/$HASHING_ALGORITHM/g" params-api.json
sed -i "s/\${{secrets.LOGZIO_TOKEN}}/$LOGZIO_TOKEN/g" params-api.json

echo "Secrets replaced successfully"
