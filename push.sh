#!/bin/bash
set -e

ACR_NAME=agenticacr001
IMAGE_NAME=agentic-linkedin-post-optimizer
IMAGE_TAG=$1

if [ -z "$IMAGE_TAG" ]; then
  echo "Usage: ./push.sh <tag>"
  exit 1
fi

echo "Checking if tag '$IMAGE_TAG' already exists..."

if az acr repository show-tags \
  --name $ACR_NAME \
  --repository $IMAGE_NAME \
  --query "[?@=='$IMAGE_TAG']" \
  --output tsv | grep -q .; then
  echo "ERROR: Tag '$IMAGE_TAG' already exists. Tags are immutable."
  exit 1
fi

docker build -t $ACR_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG .
docker push $ACR_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG

echo "Pushed $IMAGE_TAG successfully."
