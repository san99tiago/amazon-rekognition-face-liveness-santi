#!/bin/bash

# DEPLOY STEPS!!!!
export AWS_DEFAULT_REGION=us-east-1
export RFL_STACK_NAME=rufus-bank-rek-face-liveness

python3 -m venv .venv
source .venv/bin/activate

bash ./one-click.sh

# MANUAL POST-DEPLOY STEPS!!!!
# > Replace the "aws-exports.js" file with the correct Amazon Cognito IDs and endpoints.
# TODO: Add REACT_APP_ENV_API_URL to the "aws-exports.js" file.
export REACT_APP_ENV_API_URL=https://v0onolh284.execute-api.us-east-1.amazonaws.com/prod/

# Build the frontend
cd frontend
npm run build


# MANUAL STEPS TO DEPLOY FRONTEND TO AMPLIFY (MANUAL WHILE I AUTOMATE THIS...)
# > Compress the "build" output folder (select all from inside it), make ZIP file..
# > Go to the Amplify Console, and upload the ZIP file...
# > Add DNS Sub-Domain in the Amplify Console. (exclude root!!)
