#!/build/bash

PRODUCT="site24x7"
IMAGE_NAME="apminsight-pythonagent"
TAG_NAME=$1
PLATFORMS="linux/arm64,linux/amd64,linux/386"


if [ -z "$1" ]; then
    echo "TAG_NAME is not provided, Command Usage: $0 <TAG_NAME> $1 <BUILD_URL>"
    TAG_NAME="latest"
    exit 1
fi


BUILD_URL=$2
if [ -z "$2" ]; then
  echo "BUILD_URL Is not provided, Command Usage: $0 <TAG_NAME> $1 <BUILD_URL>"
  exit 1
fi

PYTHON_AGENT_FILE_NAME="apminsight-agentpython.zip"

wget -O "$PYTHON_AGENT_FILE_NAME" "$BUILD_URL"
unzip -o $PYTHON_AGENT_FILE_NAME


docker buildx create --name $IMAGE_NAME

docker buildx use $IMAGE_NAME

docker buildx build --platform  $PLATFORMS -t $PRODUCT/$IMAGE_NAME:$TAG_NAME --push .

docker buildx rm $IMAGE_NAME

rm -r apminsight-agentpython*
