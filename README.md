# SLA测试

长期可靠性测试。
基础环境为k8s环境，节点配置为4c8g。

## 依赖

* [docker](https://docs.docker.com/engine/install/)
* [python3](https://www.python.org/downloads/)
* [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/)
* [cloud-cli](https://github.com/cita-cloud/cloud-cli)

```
pip install toml
```

## 部署

当前版本为v6.7.3。

### 生成链配置

环境变量设置，参见`env.sh`:

```bash
$ cat ./env.sh
#!/bin/bash

unset DOCKER_REGISTRY
unset DOCKER_REPO
unset RELEASE_VERSION
unset CHIAN_TYPE
unset CHAIN_NAME
unset SC
unset PVC_MODE
unset NAME_SPACE
unset JAEGER_AGENT_ENDPOINT
unset S3_ENDPOINT
unset S3_ACCESS_KEY
unset S3_SECRET_KEY
unset S3_BUCKET_NAME
unset S3_REGION
unset S3_ROOT
unset SERVICE_TYPE

# 设置镜像仓库
# export DOCKER_REGISTRY=docker.io
# export DOCKER_REPO=citacloud
export DOCKER_REGISTRY=registry.devops.rivtower.com
export DOCKER_REPO=cita-cloud

# 设置链的版本
export RELEASE_VERSION=latest

# 设置链的共识类型和链的名称
# raft or overlord
export CHIAN_TYPE=overlord
export CHAIN_NAME=sla-$CHIAN_TYPE

# 设置基础环境的Storage Class和PVC access mode
export SC=local-path
export PVC_MODE=ReadWriteOnce

# 设置要使用的NameSpace
export NAME_SPACE=cita

# 是否开启交易持久化功能，如果开启则设置为1，否则不设置
export ENABLE_TX_PERSISTENCE=

# 设置jager agent endpoint，如果不使用链路追踪功能则不设置该变量
#export JAEGER_AGENT_ENDPOINT=jaeger.tracing.svc:6831

# 设置S3相关的参数，用于storage_opendal第三层
export S3_ENDPOINT=
export S3_ACCESS_KEY=
export S3_SECRET_KEY=
export S3_BUCKET_NAME=
# 通常opendal会通过endpoint自动获取region，如果是自建s3服务，自动获取不了的情况下才需要设置region
export S3_REGION=
export S3_ROOT=
# s3/oss(aliyun)/obs(huawei)/cos(tencent)/azblob(azure)
export SERVICE_TYPE=
```

生成配置文件：

```bash
$ ./gen.sh
gen config for overlord chain: 4 consensus and 1 readonly
node_address: 5ea1d94b5e405f18e7e5f8558dceae6e09e13058 validator_address: a8b7802c2d79b87624fee40c2c4dcf25eb4aeaf1723032f32f9fb1e0d671af997bc97af02492719c58fc9ed5b65a6f87
node_address: 76c8940d4868f2f6cfaef3b795239ef21b8ab512 validator_address: 81cf242de468b38b89f12ff3691500068406e3efec75755ec1572fcf7da8bd6743761971b5a19d33b74716ddac3bef48
node_address: 3990752e3978a03791058e8aea3bd913c93606ee validator_address: b611e4e9c93bd2ea38542bdd0ac07a43952f37ca8dbc57a26d477c570f6cae32f2c155ef9a36f014eae9316895ef5731
node_address: 8c290cbb42a58233051401ce63d4373f759db790 validator_address: 8617542d2209cfbfea817d27e1b23187528fb0c9b2b61e307eca188fd40540177c28908919ce7c23f37c8f7e6dbea941
node_address: 31406f8b66a0d0e10a677f3340a3d558548a0c8b validator_address: a07f048cb253c475f97f717be4717cac94480d9c3a9108117dfa0e7d009c2932de17268a346e593bec709a317c7c9724
```

### 部署链

```bash
$ ./apply.sh
apply overlord chain: 4 consensus and 1 readonly
configmap/sla-overlord-node0-account created
configmap/sla-overlord-node0-config created
service/sla-overlord-node0 created
statefulset.apps/sla-overlord-node0 created
configmap/sla-overlord-node1-account created
configmap/sla-overlord-node1-config created
service/sla-overlord-node1 created
statefulset.apps/sla-overlord-node1 created
configmap/sla-overlord-node2-account created
configmap/sla-overlord-node2-config created
service/sla-overlord-node2 created
statefulset.apps/sla-overlord-node2 created
configmap/sla-overlord-node3-account created
configmap/sla-overlord-node3-config created
service/sla-overlord-node3 created
statefulset.apps/sla-overlord-node3 created
configmap/sla-overlord-node4-account created
configmap/sla-overlord-node4-config created
service/sla-overlord-node4 created
statefulset.apps/sla-overlord-node4 created
```

### 停链

```bash
$ ./delete.sh
delete overlord chain: 4 consensus and 1 readonly
configmap "sla-overlord-node0-account" deleted
configmap "sla-overlord-node0-config" deleted
service "sla-overlord-node0" deleted
statefulset.apps "sla-overlord-node0" deleted
configmap "sla-overlord-node1-account" deleted
configmap "sla-overlord-node1-config" deleted
service "sla-overlord-node1" deleted
statefulset.apps "sla-overlord-node1" deleted
configmap "sla-overlord-node2-account" deleted
configmap "sla-overlord-node2-config" deleted
service "sla-overlord-node2" deleted
statefulset.apps "sla-overlord-node2" deleted
configmap "sla-overlord-node3-account" deleted
configmap "sla-overlord-node3-config" deleted
service "sla-overlord-node3" deleted
statefulset.apps "sla-overlord-node3" deleted
configmap "sla-overlord-node4-account" deleted
configmap "sla-overlord-node4-config" deleted
service "sla-overlord-node4" deleted
statefulset.apps "sla-overlord-node4" deleted
```

## 运维测试

操作前要先设置环境变量：

```bash
# 设置环境变量
source ./env.sh
```

### 升级版本

采用通用的底链升级策略，视具体版本的情况，可能需要一些额外的变更操作。

升级配置：

```bash
# 修改env.sh，设置要升级的新版本版本号
bash -x upgrade.sh
```

然后重新部署即可。

### 回滚节点

替换节点容器镜像为`cloud-op`。
```sehll
kubectl patch sts sla-overlord-node4 -n $NAME_SPACE --type json --patch '
[
	{
		"op" : "replace" ,
		"path" : "/spec/template/spec/containers" ,
		"value" : [
			{
				"name": "patch-op",
				"image": "registry.devops.rivtower.com/cita-cloud/cloud-op",
				"command": [
					"sleep",
					"infinity"
				],
				"imagePullPolicy": "Always",
				"volumeMounts": [
					{
						"mountPath": "/data",
						"name": "datadir"
					},
					{
						"mountPath": "/etc/cita-cloud/config",
						"name": "node-config"
					},
					{
						"mountPath": "/mnt",
						"name": "node-account"
					}
				],
				"workingDir": "/data"
			}
		]
	}
]'
```

待节点重启完成后，执行回滚操作。

```bash
kubectl exec -n $NAME_SPACE -it sla-overlord-node4-0 -c patch-op -- cloud-op rollback -c /etc/cita-cloud/config/config.toml -n /data 240000
```

恢复节点

```bash
kubectl rollout undo -n $NAME_SPACE sts sla-overlord-node4
```

### 备份节点数据

创建存放备份数据的`PVC`。如果之前已经创建过则跳过该步骤。

```bash
cat << EOF > backup_pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: backup
spec:
  storageClassName: local-path
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10G
EOF

kubectl apply -n $NAME_SPACE -f backup_pvc.yaml
```

替换节点容器镜像为`cloud-op`，并增加挂载备份`PVC`。

```bash
kubectl patch sts sla-overlord-node4 -n $NAME_SPACE --type json --patch '
[
	{
		"op" : "replace" ,
		"path" : "/spec/template/spec/containers" ,
		"value" : [
			{
				"name": "patch-op",
				"image": "registry.devops.rivtower.com/cita-cloud/cloud-op",
				"command": [
					"sleep",
					"infinity"
				],
				"imagePullPolicy": "Always",
				"volumeMounts": [
					{
						"mountPath": "/data",
						"name": "datadir"
					},
					{
						"mountPath": "/etc/cita-cloud/config",
						"name": "node-config"
					},
					{
						"mountPath": "/mnt",
						"name": "node-account"
					},
					{
						"mountPath": "/backup",
						"name": "backup"
					}
				],
				"workingDir": "/data"
			}
		]
	},
	{
		"op" : "add" ,
		"path" : "/spec/template/spec/volumes/-" ,
		"value" : {
			"name": "backup",
			"persistentVolumeClaim": {
				"claimName": "backup"
			}
		}
	}
]'
```

待节点重启完成后，执行备份操作。

```bash
# 拷贝的方式进行备份
kubectl exec -n $NAME_SPACE -it sla-overlord-node4-0 -c patch-op -- cloud-op backup -c /etc/cita-cloud/config/config.toml -p /backup -n /data 250000

# 或者
# 导出导入的方式进行备份
# 支持对一段高度区间的导出，所以可以做增量备份，但是必须保证按照高度增长顺序且区间连续无空缺
kubectl exec -n $NAME_SPACE -it sla-overlord-node4-0 -c patch-op -- cloud-op export -c /etc/cita-cloud/config/config.toml -p /backup/export -n /data -b 0 -e 250000
```

恢复节点

```bash
kubectl rollout undo -n $NAME_SPACE sts sla-overlord-node4
```

### 从备份恢复节点数据

停止要恢复的节点

```bash
kubectl scale sts sla-overlord-node4 -n $NAME_SPACE --replicas=0
```

创建临时`pod`从备份恢复节点数据。
```bash
kubectl run restore -n cita --overrides='
{
  "spec": {
    "containers": [
      {
        "name": "restore",
        "image": "busybox",
        "command": ["/bin/sh"],
        "args": ["-c", "rm -rf /data/chain_data; rm -rf /data/data; cp -af /backup/250000/chain_data /data; cp -af /backup/250000/data /data"],
        "volumeMounts": [
          {
            "mountPath": "/backup",
            "name": "backup"
          },
          {
            "mountPath": "/data",
            "name": "data"
          }
        ]
      }
    ],
    "volumes": [
      {
        "name": "backup",
        "persistentVolumeClaim": {
        "claimName": "backup"
        }
      },
      {
        "name": "data",
        "persistentVolumeClaim": {
        "claimName": "datadir-sla-overlord-node4-0"
        }
      }
    ]
  }
}
'  --image=busybox --restart=Never
```

恢复其实就是简单的文件拷贝，需要注意：

1. `backup`子命令备份的时候会自动添加以备份高度命名的子文件夹，因此这里使用的路径是`/backup/250000/`。
2. `export`子命令导出不会添加子文件夹，因此要用导出的数据进行恢复的话，这里的路径应该是`/backup/export/`。
3. 注意文件的权限，防止恢复之后节点没有权限读取而启动失败，必要时可以手工更改一下。 

等待命令执行完成，删除临时`pod`并恢复节点

```bash
kubectl delete pod restore -n $NAME_SPACE
kubectl scale sts sla-overlord-node4 -n $NAME_SPACE --replicas=1
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
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --domain node0
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --domain node1
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --domain node2
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --domain node3
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --domain node4
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --domain node5
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
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --domain node0
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --domain node1
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --domain node2
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --domain node3
docker run -it --rm -v $(pwd):/data -w /data $DOCKER_REGISTRY/$DOCKER_REPO/cloud-config:$RELEASE_VERSION cloud-config update-yaml --chain-name $CHAIN_NAME --storage-class $SC --docker-registry $DOCKER_REGISTRY --docker-repo $DOCKER_REPO --domain node4
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

操作前要先设置环境变量：

```bash
# 设置环境变量
source ./env.sh
```

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

