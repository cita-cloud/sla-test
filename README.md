# SLA测试

长期可靠性测试。
基础环境为k8s环境，有5个work节点，配置为4c8g。
链配置为4个共识节点1个只读节点。

## 依赖

* docker
* python3
* kubectl
* cldi

```bash
pip install kubernetes tenacity
```

## 部署

初始版本为v6.6.1。

### 生成链配置

环境变量设置：

```bash
# 设置docker镜像仓库
export DOCKER_REGISTRY=docker.io
export DOCKER_REPO=citacloud
# export DOCKER_REGISTRY=registry.devops.rivtower.com
# export DOCKER_REPO=cita-cloud

# 设置链的版本
export RELEASE_VERSION=v6.6.1

# 设置链的类型和名称
export CHIAN_TYPE=bft
# export CHIAN_TYPE=raft
# export CHIAN_TYPE=overlord
export CHAIN_NAME=sla-$CHIAN_TYPE

# 设置基础环境的Storage Class
export SC=ceph-filesystem

export NAME_SPACE=cita-cloud-sla
```

生成配置文件：

```bash
# 生成初始的4个共识节点配置
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config create-k8s --chain-name $CHAIN_NAME --admin 0x9bab5858df4a9e84ff3958884a01a4fce5e07edb --nodelist localhost:40000:node0:k8s,localhost:40001:node1:k8s,localhost:40002:node2:k8s,localhost:40003:node3:k8s --controller_tag $RELEASE_VERSION --consensus_image consensus_$CHIAN_TYPE --consensus_tag $RELEASE_VERSION --crypto_tag $RELEASE_VERSION --network_tag $RELEASE_VERSION --storage_tag $RELEASE_VERSION --executor_tag $RELEASE_VERSION

# 增加一个只读节点的配置
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config append-k8s --chain-name $CHAIN_NAME --node localhost:40004:node4:k8s

# 生成所有节点配置的yaml文件
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --requests-cpu 120m --limits-cpu 1 --requests-memory 240Mi --limits-memory 2Gi --domain node0
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --requests-cpu 120m --limits-cpu 1 --requests-memory 240Mi --limits-memory 2Gi --domain node1
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --requests-cpu 120m --limits-cpu 1 --requests-memory 240Mi --limits-memory 2Gi --domain node2
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --requests-cpu 120m --limits-cpu 1 --requests-memory 240Mi --limits-memory 2Gi --domain node3
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --requests-cpu 120m --limits-cpu 1 --requests-memory 240Mi --limits-memory 2Gi --domain node4
```

### 部署链

```bash
kubectl create ns $NAME_SPACE
kubectl apply -f $CHAIN_NAME-node0/yamls/ -n $NAME_SPACE
kubectl apply -f $CHAIN_NAME-node1/yamls/ -n $NAME_SPACE
kubectl apply -f $CHAIN_NAME-node2/yamls/ -n $NAME_SPACE
kubectl apply -f $CHAIN_NAME-node3/yamls/ -n $NAME_SPACE
kubectl apply -f $CHAIN_NAME-node4/yamls/ -n $NAME_SPACE
```

### 部署节点负载均衡

```bash
# 提前设置好 CHAIN_NAME/NAME_SPACE 环境变量
envsubst < lb/envoy-deployment.yaml | kubectl apply -n $NAME_SPACE -f -
```

负载均衡暴露到`$NAME_SPACE`命名空间下，名为`$CHAIN_NAME-envoy`的SVC，端口有：
* 60004 - 链的RPC端口
* 60002 - 链的Call端口
* 9901  - envoy的管理端口

### 部署缓存服务

```bash
# 提前设置好 CHAIN_NAME/NAME_SPACE/SC/RELEASE_VERSION 环境变量
envsubst < cache/cache-deployment.yaml | kubectl apply -n $NAME_SPACE -f -
```

缓存服务的端口暴露到`$NAME_SPACE`命名空间下，名为`$CHAIN_NAME-cache`的SVC，端口是8000。

## 常规测试

### 部署测试

```bash
# 提前设置好 CHAIN_NAME/NAME_SPACE/SC/RELEASE_VERSION 环境变量
envsubst < client/client-deployment.yaml | kubectl apply -n $NAME_SPACE -f -
```

采集结果的端口暴露到`$NAME_SPACE`命名空间下，名为`$CHAIN_NAME-sla-test-client`的SVC，端口是61616。

### 查看结果

## 运维测试

### 升级版本

采用通用的底链升级策略，视具体版本的情况，可能需要一些额外的变更操作。

### 备份节点数据

```bash
# 提前设置好 CHAIN_NAME/NAME_SPACE/SC/DOCKER_REGISTRY/DOCKER_REPO 环境变量
python3 ./script/backup.py
```

### 从备份恢复节点数据

```bash
# 提前设置好 CHAIN_NAME/NAME_SPACE/DOCKER_REGISTRY/DOCKER_REPO 环境变量
python3 ./script/restore.py
```

### 消块

### 快照

### 从快照恢复节点数据

### 守护节点切换

### 增加只读节点

### 提升只读节点为共识节点

### 降级共识节点为普通节点

### 删除节点

### 存储扩容

跟具体使用的存储系统有关。

## 压力测试
以400tps发送nft合约的mint交易

## 故障演练

### 重启

重启1个节点

重启所有节点

### 网络故障

### 文件损坏

