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

# MANUAL STEP
# > Entered the Cognito Identity Pool and I updated it with user access with the same IAM Role policy as the one for guests.
# > I manually added the Auth approach with the same role
