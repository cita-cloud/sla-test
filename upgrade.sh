#! /bin/bash

set -e

source ./env.sh

# 修改配置stage，可以重新修改链配置
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config set-stage --chain-name $CHAIN_NAME --stage init

# 获取之前链的一些关键信息，以便复用
TIMESTAMP=$(python3 -c 'import toml;import os; config = "{}/chain_config.toml".format(os.getenv("CHAIN_NAME")); print (toml.load(config)["genesis_block"]["timestamp"]);')
CHAIN_ID=$(python3 -c 'import toml;import os; config = "{}/chain_config.toml".format(os.getenv("CHAIN_NAME")); print (toml.load(config)["system_config"]["chain_id"]);')
ADMIN=$(python3 -c 'import toml;import os; config = "{}/chain_config.toml".format(os.getenv("CHAIN_NAME")); print (toml.load(config)["system_config"]["admin"]);')
VALIDATORS=$(python3 -c 'import toml;import os; config = "{}/chain_config.toml".format(os.getenv("CHAIN_NAME")); print (",".join(toml.load(config)["system_config"]["validators"]));')

# 初始化链级配置，chain_id和timestamp跟升级前保持一致
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config init-chain-config --chain-name $CHAIN_NAME --chain_id $CHAIN_ID --consensus_image consensus_$CHIAN_TYPE --consensus_tag $RELEASE_VERSION --controller_tag $RELEASE_VERSION --executor_tag $RELEASE_VERSION --network_tag $RELEASE_VERSION --storage_tag $RELEASE_VERSION --timestamp $TIMESTAMP

# 设置admin，与升级前保持一致
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config set-admin --chain-name $CHAIN_NAME --admin $ADMIN

# 设置validator列表，与升级前保持一致
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config set-validators --chain-name $CHAIN_NAME --validators $VALIDATORS

# 链级配置修改完成，设置stage
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config set-stage --chain-name $CHAIN_NAME

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
    # 设置节点列表，共识节点和只读节点都在内
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config set-nodelist --chain-name $CHAIN_NAME --nodelist localhost:40000:node0:k8s:$NAME_SPACE,localhost:40001:node1:k8s:$NAME_SPACE,localhost:40002:node2:k8s:$NAME_SPACE,localhost:40003:node3:k8s:$NAME_SPACE,localhost:40004:node4:k8s:$NAME_SPACE

    # 重新初始化所有节点，前四个为共识节点，最后一个为只读节点
    # 节点目录下没有账户信息，把账户信息重新拷贝回去
    cp -rf $CHAIN_NAME-node0/accounts/* $CHAIN_NAME/accounts/
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config init-node --chain-name $CHAIN_NAME --domain node0 --account $(python3 -c 'import toml;import os; config = "{}-node0/node_config.toml".format(os.getenv("CHAIN_NAME")); print (toml.load(config)["account"]);') $EXTRA_ARGS
    cp -rf $CHAIN_NAME-node1/accounts/* $CHAIN_NAME/accounts/
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config init-node --chain-name $CHAIN_NAME --domain node1 --account $(python3 -c 'import toml;import os; config = "{}-node1/node_config.toml".format(os.getenv("CHAIN_NAME")); print (toml.load(config)["account"]);') $EXTRA_ARGS
    cp -rf $CHAIN_NAME-node2/accounts/* $CHAIN_NAME/accounts/
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config init-node --chain-name $CHAIN_NAME --domain node2 --account $(python3 -c 'import toml;import os; config = "{}-node2/node_config.toml".format(os.getenv("CHAIN_NAME")); print (toml.load(config)["account"]);') $EXTRA_ARGS
    cp -rf $CHAIN_NAME-node3/accounts/* $CHAIN_NAME/accounts/
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config init-node --chain-name $CHAIN_NAME --domain node3 --account $(python3 -c 'import toml;import os; config = "{}-node3/node_config.toml".format(os.getenv("CHAIN_NAME")); print (toml.load(config)["account"]);') $EXTRA_ARGS
    cp -rf $CHAIN_NAME-node4/accounts/* $CHAIN_NAME/accounts/
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config init-node --chain-name $CHAIN_NAME --domain node4 --account $(python3 -c 'import toml;import os; config = "{}-node4/node_config.toml".format(os.getenv("CHAIN_NAME")); print (toml.load(config)["account"]);') $EXTRA_ARGS

    # 生成所有节点配置文件
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-node --chain-name $CHAIN_NAME --domain node0
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-node --chain-name $CHAIN_NAME --domain node1
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-node --chain-name $CHAIN_NAME --domain node2
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-node --chain-name $CHAIN_NAME --domain node3
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-node --chain-name $CHAIN_NAME --domain node4

    #生成所有节点yaml文件
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --access-mode=$PVC_MODE --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --enable-kustomize --domain node0
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --access-mode=$PVC_MODE --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --enable-kustomize --domain node1
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --access-mode=$PVC_MODE --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --enable-kustomize --domain node2
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --access-mode=$PVC_MODE --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --enable-kustomize --domain node3
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --access-mode=$PVC_MODE --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --enable-kustomize --domain node4
fi

if [ $CHIAN_TYPE == "raft" ]
then
    # 设置节点列表，共识节点和只读节点都在内
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config set-nodelist --chain-name $CHAIN_NAME --nodelist localhost:40000:node0:k8s:$NAME_SPACE,localhost:40001:node1:k8s:$NAME_SPACE,localhost:40002:node2:k8s:$NAME_SPACE,localhost:40003:node3:k8s:$NAME_SPACE

    # 重新初始化所有节点，前三个为共识节点，最后一个为只读节点
    # 节点目录下没有账户信息，把账户信息重新拷贝回去
    cp -rf $CHAIN_NAME-node0/accounts/* $CHAIN_NAME/accounts/
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config init-node --chain-name $CHAIN_NAME --domain node0 --account $(python3 -c 'import toml;import os; config = "{}-node0/node_config.toml".format(os.getenv("CHAIN_NAME")); print (toml.load(config)["account"]);') $EXTRA_ARGS
    cp -rf $CHAIN_NAME-node1/accounts/* $CHAIN_NAME/accounts/
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config init-node --chain-name $CHAIN_NAME --domain node1 --account $(python3 -c 'import toml;import os; config = "{}-node1/node_config.toml".format(os.getenv("CHAIN_NAME")); print (toml.load(config)["account"]);') $EXTRA_ARGS
    cp -rf $CHAIN_NAME-node2/accounts/* $CHAIN_NAME/accounts/
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config init-node --chain-name $CHAIN_NAME --domain node2 --account $(python3 -c 'import toml;import os; config = "{}-node2/node_config.toml".format(os.getenv("CHAIN_NAME")); print (toml.load(config)["account"]);') $EXTRA_ARGS
    cp -rf $CHAIN_NAME-node3/accounts/* $CHAIN_NAME/accounts/
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config init-node --chain-name $CHAIN_NAME --domain node3 --account $(python3 -c 'import toml;import os; config = "{}-node3/node_config.toml".format(os.getenv("CHAIN_NAME")); print (toml.load(config)["account"]);') $EXTRA_ARGS

    # 生成所有节点配置文件
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-node --chain-name $CHAIN_NAME --domain node0
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-node --chain-name $CHAIN_NAME --domain node1
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-node --chain-name $CHAIN_NAME --domain node2
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-node --chain-name $CHAIN_NAME --domain node3

    #生成所有节点yaml文件
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --access-mode=$PVC_MODE --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --enable-kustomize --domain node0
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --access-mode=$PVC_MODE --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --enable-kustomize --domain node1
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --access-mode=$PVC_MODE --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --enable-kustomize --domain node2
    docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --access-mode=$PVC_MODE --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --enable-kustomize --domain node3
fi
