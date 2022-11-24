# SLA测试

长期可靠性测试。
基础环境为k8s环境，有5个work节点，配置为4c8g。
链配置为4个共识节点1个只读节点。

## 依赖

* [docker](https://docs.docker.com/engine/install/)
* [python3](https://www.python.org/downloads/)
* [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/)
* [helm](https://helm.sh/docs/intro/install/)
* [cloud-cli](https://github.com/cita-cloud/cloud-cli)
* [cita-node-operator](https://github.com/cita-cloud/cita-node-operator)

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

### 安装Operator

后续运维操作需要依赖`cita-node-operator`。

```
helm repo add cita-node-operator https://cita-cloud.github.io/cita-node-operator
helm install cita-node-operator cita-node-operator/cita-node-operator -n=$NAME_SPACE
```

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

升级配置：

```bash
# 设置要升级的新版本版本号
export RELEASE_VERSION=v6.6.2
bash -x ./upgrade/upgrade.sh
```

然后重新部署即可。

### 备份节点数据

```shell
# 提前设置好 CHAIN_NAME/NAME_SPACE/SC/DOCKER_REGISTRY/DOCKER_REPO 环境变量
python3 ./script/backup.py -n node4
```

### 从备份恢复节点数据

```shell
# 提前设置好 CHAIN_NAME/NAME_SPACE/DOCKER_REGISTRY/DOCKER_REPO 环境变量
python3 ./script/restore.py -n node0 -m backup
```

### 消块

```shell
# 提前设置好 CHAIN_NAME/NAME_SPACE/DOCKER_REGISTRY/DOCKER_REPO 环境变量
python3 ./script/block_height_fallback.py -n node0 -b 100
```

### 快照

```shell
# 提前设置好 CHAIN_NAME/NAME_SPACE/DOCKER_REGISTRY/DOCKER_REPO 环境变量
python3 ./script/snapshot.py -n node4 -b 200
```

### 从快照恢复节点数据

```shell
# 提前设置好 CHAIN_NAME/NAME_SPACE/DOCKER_REGISTRY/DOCKER_REPO 环境变量
python3 ./script/restore.py -n node0 -m snapshot
```

### 守护节点切换

```bash
# 提前设置好 CHAIN_NAME/NAME_SPACE/DOCKER_REGISTRY/DOCKER_REPO 环境变量
python3 ./script/switchover.py -s node0 -d node4
```

### 节点操作

#### 增加只读节点

```bash
# 链级配置目录下的私钥没有上传到仓库
# 需要从节点目录下恢复
cp $CHAIN_NAME-node0/ca_cert/key.pem $CHAIN_NAME/ca_cert/

# 增加一个只读节点的配置
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config append-k8s --chain-name $CHAIN_NAME --node localhost:40005:node5:k8s

# 更新所有节点配置的yaml文件
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --requests-cpu 120m --limits-cpu 1 --requests-memory 240Mi --limits-memory 2Gi --domain node0
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --requests-cpu 120m --limits-cpu 1 --requests-memory 240Mi --limits-memory 2Gi --domain node1
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --requests-cpu 120m --limits-cpu 1 --requests-memory 240Mi --limits-memory 2Gi --domain node2
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --requests-cpu 120m --limits-cpu 1 --requests-memory 240Mi --limits-memory 2Gi --domain node3
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --requests-cpu 120m --limits-cpu 1 --requests-memory 240Mi --limits-memory 2Gi --domain node4
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --requests-cpu 120m --limits-cpu 1 --requests-memory 240Mi --limits-memory 2Gi --domain node5
```

重新部署所有节点

```bash
kubectl apply -f $CHAIN_NAME-node0/yamls/ -n $NAME_SPACE
kubectl apply -f $CHAIN_NAME-node1/yamls/ -n $NAME_SPACE
kubectl apply -f $CHAIN_NAME-node2/yamls/ -n $NAME_SPACE
kubectl apply -f $CHAIN_NAME-node3/yamls/ -n $NAME_SPACE
kubectl apply -f $CHAIN_NAME-node4/yamls/ -n $NAME_SPACE
kubectl apply -f $CHAIN_NAME-node5/yamls/ -n $NAME_SPACE
```

等待网络配置文件变更生效，以及新节点同步完成（这里也可以用备份加速同步）。

#### 提升只读节点为共识节点

```bash
# 转发node0的rpc端口到本地：
kubectl port-forward -n $NAME_SPACE pod/${CHAIN_NAME}-node0-0 50004 50002

# 设置cldi
cldi account import 0xb2371a70c297106449f89445f20289e6d16942f08f861b5e95cbcf0462e384c1 --name admin --crypto SM
cldi -r 127.0.0.1:50004 -e 127.0.0.1:50002 -u admin context save default

# 获取当前validator列表
VALIDATORS=$(python3 -c 'import toml;import os; config = "{}/chain_config.toml".format(os.getenv("CHAIN_NAME")); print (" ".join(toml.load(config)["system_config"]["validators"]));')

# 获取node5的validator地址
NODE5_ACCOUNT=$(python3 -c 'import toml;import os; config = "{}-node5/node_config.toml".format(os.getenv("CHAIN_NAME")); print (toml.load(config)["account"]);')
NODE5_VALIDATOR=$(cat $CHAIN_NAME/accounts/$NODE5_ACCOUNT/validator_address)

# 将node5加入validator列表
cldi admin update-validators $VALIDATORS $NODE5_VALIDATOR
```

等待交易确认之后，node5就应该开始参与共识。

#### 降级共识节点为普通节点

```bash
# 将node5剔除出validator列表
# 这里就直接应用之前的validator列表
cldi admin update-validators $VALIDATORS
```

等待交易确认之后，node5就不再参与共识。

#### 删除节点

停掉node5
```bash
kubectl delete -f ${CHAIN_NAME}-node5/yamls/ -n $NAME_SPACE
```

对应的pvc不会自动删除，如果需要，可以手工清除
```bash
kubectl delete pvc -n $NAME_SPACE datadir-${CHAIN_NAME}-node5-0
```

此时，其他节点中还存在着node5的节点信息，需要从链的配置中删除node5

```bash
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config delete-k8s --chain-name $CHAIN_NAME --domain node5

# 更新所有节点配置的yaml文件
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --requests-cpu 120m --limits-cpu 1 --requests-memory 240Mi --limits-memory 2Gi --domain node0
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --requests-cpu 120m --limits-cpu 1 --requests-memory 240Mi --limits-memory 2Gi --domain node1
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --requests-cpu 120m --limits-cpu 1 --requests-memory 240Mi --limits-memory 2Gi --domain node2
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --requests-cpu 120m --limits-cpu 1 --requests-memory 240Mi --limits-memory 2Gi --domain node3
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --requests-cpu 120m --limits-cpu 1 --requests-memory 240Mi --limits-memory 2Gi --domain node4
```

重新部署所有节点

```bash
kubectl apply -f $CHAIN_NAME-node0/yamls/ -n $NAME_SPACE
kubectl apply -f $CHAIN_NAME-node1/yamls/ -n $NAME_SPACE
kubectl apply -f $CHAIN_NAME-node2/yamls/ -n $NAME_SPACE
kubectl apply -f $CHAIN_NAME-node3/yamls/ -n $NAME_SPACE
kubectl apply -f $CHAIN_NAME-node4/yamls/ -n $NAME_SPACE
```

等待网络配置文件变更生效，其他节点中就不存在node5的节点信息了。

### 存储扩容

跟具体使用的存储系统有关。

## 压力测试
发送合约交易

```bash
# 创建合约，得到交易哈希
$ cldi create 0x608060405234801561001057600080fd5b5060f58061001f6000396000f3006080604052600436106053576000357c0100000000000000000000000000000000000000000000000000000000900463ffffffff16806306661abd1460585780634f2be91f146080578063d826f88f146094575b600080fd5b348015606357600080fd5b50606a60a8565b6040518082815260200191505060405180910390f35b348015608b57600080fd5b50609260ae565b005b348015609f57600080fd5b5060a660c0565b005b60005481565b60016000808282540192505081905550565b600080819055505600a165627a7a72305820faa1d1f51d7b5ca2b200e0f6cdef4f2d7e44ee686209e300beb1146f40d32dee0029

0x24aad208ec05b123896af072693bb883db29345030b54b1978c0a6a830d2846e

# 根据交易哈希查询交易回执
$ cldi get receipt 0x24aad208ec05b123896af072693bb883db29345030b54b1978c0a6a830d2846e
{
  "block_hash": "0xc6cba077b6be63f35952454de1a3401f03d074e075b8f9409f02bdc12f738c9d",
  "block_number": 24474,
  "contract_addr": "0x0a2d38fad976b007e62d140393d331bf7de10bef",
  "cumulative_quota_used": "0x0000000000000000000000000000000000000000000000000000000000018ed3",
  "error_msg": "",
  "logs": [],
  "logs_bloom": "0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
  "quota_used": "0x0000000000000000000000000000000000000000000000000000000000018ed3",
  "state_root": "0x2c5ee85fa933c56f040f54d8f45ee8d13c04d66f6a756dda1806247d77757274",
  "tx_hash": "0x24aad208ec05b123896af072693bb883db29345030b54b1978c0a6a830d2846e",
  "tx_index": 0
}

# 其中contract_addr即创建的合约的地址，发送合约交易
$ cldi bench send -c 1 -t 0x0a2d38fad976b007e62d140393d331bf7de10bef -d 0x4f2be91f -q 800000 10000
Preparing connections and transactions..
Sending transactions..
  [00:00:28] [===============================================================================================================================================================================================================================================================]   10000/10000  `10000` tasks finished in `28720` ms
`10000` success, `0` failure
00:00 block `26031` contains `0` txs, finalized: `0`
00:05 block `26032` contains `177` txs, finalized: `177`
00:06 block `26033` contains `191` txs, finalized: `368`
00:09 block `26034` contains `1062` txs, finalized: `1430`
00:12 block `26035` contains `1036` txs, finalized: `2466`
00:17 block `26036` contains `1342` txs, finalized: `3808`
00:18 block `26037` contains `820` txs, finalized: `4628`
00:21 block `26038` contains `1007` txs, finalized: `5635`
00:24 block `26039` contains `1065` txs, finalized: `6700`
00:29 block `26040` contains `1342` txs, finalized: `8042`
00:30 block `26041` contains `765` txs, finalized: `8807`
00:33 block `26042` contains `1098` txs, finalized: `9905`
00:36 block `26043` contains `95` txs, finalized: `10000`

`10000` txs finalized in `36` secs, `277.78` tx/s
```

循环调用以上命令即可实现一段时间的压力测试。

## 故障演练

### 重启

重启1个节点

```bash
kubectl delete -n $NAME_SPACE pod $CHAIN_NAME-node0-0
```

重启所有节点

```bash
kubectl delete -n $NAME_SPACE pod $CHAIN_NAME-node0-0
kubectl delete -n $NAME_SPACE pod $CHAIN_NAME-node1-0
kubectl delete -n $NAME_SPACE pod $CHAIN_NAME-node2-0
kubectl delete -n $NAME_SPACE pod $CHAIN_NAME-node3-0
kubectl delete -n $NAME_SPACE pod $CHAIN_NAME-node4-0
```

### 网络故障

### 文件损坏

