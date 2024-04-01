#!/bin/bash

set -e

# 设置环境变量
source ./env.sh

# init-node的一些额外的参数
EXTRA_ARGS=""
if [ $ENABLE_TX_PERSISTENCE ]
then
    EXTRA_ARGS="$EXTRA_ARGS --enable-tx-persistence"
fi
if [ $JAEGER_AGENT_ENDPOINT ]
then
    EXTRA_ARGS="$EXTRA_ARGS --jaeger-agent-endpoint $JAEGER_AGENT_ENDPOINT"
fi
if [ $S3_ENDPOINT ] && [ $S3_ACCESS_KEY ] && [ $S3_SECRET_KEY ] && [ $S3_BUCKET_NAME ] && [ $SERVICE_TYPE ]
then
    EXTRA_ARGS="$EXTRA_ARGS --access-key-id $S3_ACCESS_KEY --secret-access-key $S3_SECRET_KEY --s3-endpoint $S3_ENDPOINT --s3-bucket $S3_BUCKET_NAME --service-type $SERVICE_TYPE"
    if [ $S3_ROOT ]
    then
        EXTRA_ARGS="$EXTRA_ARGS --s3-root $S3_ROOT"
    fi
    if [ $S3_REGION ]
    then
        EXTRA_ARGS="$EXTRA_ARGS --s3-region $S3_REGION"
    fi
fi

if [ $CHIAN_TYPE == "overlord" ]
then
    echo "gen config for overlord chain: node5 readonly"
    # 增加一个只读节点的配置
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config append --chain-name $CHAIN_NAME --node localhost:40005:node5:k8s:chain-cache $EXTRA_ARGS

    # 生成节点配置的yaml文件
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --access-mode=$PVC_MODE --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --enable-kustomize --domain node5
fi

if [ $CHIAN_TYPE == "raft" ]
then
    echo "gen config for raft chain: node5 readonly"
    # 增加一个只读节点的配置
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config append --chain-name $CHAIN_NAME --node localhost:40005:node5:k8s:chain-cache  $EXTRA_ARGS

    # 生成所有节点配置的yaml文件
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --access-mode=$PVC_MODE --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --enable-kustomize --domain node5
fi
