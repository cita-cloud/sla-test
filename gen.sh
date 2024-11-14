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
if [ $EXPORTER_PATH ]
then
    EXTRA_ARGS="$EXTRA_ARGS --exporter-path $EXPORTER_PATH"
fi

if [ $CHIAN_TYPE == "overlord" ]
then
    echo "gen config for overlord chain: 4 consensus and 1 readonly"
    # 生成初始的4个共识节点配置
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config create --chain-name $CHAIN_NAME --admin 0x9bab5858df4a9e84ff3958884a01a4fce5e07edb --nodelist localhost:40000:node0:k8s:$NAME_SPACE,localhost:40001:node1:k8s:$NAME_SPACE,localhost:40002:node2:k8s:$NAME_SPACE,localhost:40003:node3:k8s:$NAME_SPACE --controller_tag $RELEASE_VERSION --consensus_image consensus_$CHIAN_TYPE --consensus_tag $RELEASE_VERSION --network_tag $RELEASE_VERSION --storage_tag $RELEASE_VERSION --executor_tag $RELEASE_VERSION $EXTRA_ARGS

    # 增加一个只读节点的配置
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config append --chain-name $CHAIN_NAME --node localhost:40004:node4:k8s:$NAME_SPACE $EXTRA_ARGS

    # 生成所有节点配置的yaml文件
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --access-mode=$PVC_MODE --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --enable-kustomize --domain node0
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --access-mode=$PVC_MODE --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --enable-kustomize --domain node1
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --access-mode=$PVC_MODE --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --enable-kustomize --domain node2
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --access-mode=$PVC_MODE --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --enable-kustomize --domain node3
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --access-mode=$PVC_MODE --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --enable-kustomize --domain node4
fi

if [ $CHIAN_TYPE == "raft" ]
then
    echo "gen config for raft chain: 3 consensus and 1 readonly"
    # 生成初始的4个共识节点配置
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config create --chain-name $CHAIN_NAME --admin 0x9bab5858df4a9e84ff3958884a01a4fce5e07edb --nodelist localhost:40000:node0:k8s:$NAME_SPACE,localhost:40001:node1:k8s:$NAME_SPACE,localhost:40002:node2:k8s:$NAME_SPACE --controller_tag $RELEASE_VERSION --consensus_image consensus_$CHIAN_TYPE --consensus_tag $RELEASE_VERSION --network_tag $RELEASE_VERSION --storage_tag $RELEASE_VERSION --executor_tag $RELEASE_VERSION  $EXTRA_ARGS
    
    # 增加一个只读节点的配置
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config append --chain-name $CHAIN_NAME --node localhost:40003:node3:k8s:$NAME_SPACE  $EXTRA_ARGS

    # 生成所有节点配置的yaml文件
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --access-mode=$PVC_MODE --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --enable-kustomize --domain node0
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --access-mode=$PVC_MODE --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --enable-kustomize --domain node1
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --access-mode=$PVC_MODE --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --enable-kustomize --domain node2
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --access-mode=$PVC_MODE --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --enable-kustomize --domain node3
fi
