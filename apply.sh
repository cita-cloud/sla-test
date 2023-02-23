#!/bin/bash

# 设置环境变量
source ./env.sh

# 创建NameSpace
kubectl create ns $NAME_SPACE

if [ $CHIAN_TYPE == "overlord" ]
then
    echo "apply overlord chain: 4 consensus and 1 readonly"
    kubectl apply -f $CHAIN_NAME-node0/yamls/ -n $NAME_SPACE
    kubectl apply -f $CHAIN_NAME-node1/yamls/ -n $NAME_SPACE
    kubectl apply -f $CHAIN_NAME-node2/yamls/ -n $NAME_SPACE
    kubectl apply -f $CHAIN_NAME-node3/yamls/ -n $NAME_SPACE
    kubectl apply -f $CHAIN_NAME-node4/yamls/ -n $NAME_SPACE
fi

if [ $CHIAN_TYPE == "raft" ]
then
    echo "apply raft chain: 3 consensus and 1 readonly"
    kubectl apply -f $CHAIN_NAME-node0/yamls/ -n $NAME_SPACE
    kubectl apply -f $CHAIN_NAME-node1/yamls/ -n $NAME_SPACE
    kubectl apply -f $CHAIN_NAME-node2/yamls/ -n $NAME_SPACE
    kubectl apply -f $CHAIN_NAME-node3/yamls/ -n $NAME_SPACE
fi
