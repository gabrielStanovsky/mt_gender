#!/bin/bash
# Usage:
#   gtranslate.sh path/to/input/file.json
# Outputs to stdout

curl -s -X POST -H "Content-Type: application/json" \
    -H "Authorization: Bearer "$(gcloud auth application-default print-access-token) \
    --data "`cat $1`" "https://translation.googleapis.com/language/translate/v2"
