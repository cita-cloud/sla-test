#!/bin/bash

# 设置环境变量
source ./env.sh

# 创建NameSpace
kubectl create ns $NAME_SPACE

if [ $CHIAN_TYPE == "overlord" ]
then
    echo "apply overlord chain: 4 consensus and 1 readonly"
    kubectl apply -k $CHAIN_NAME-node0 -n $NAME_SPACE
    kubectl apply -k $CHAIN_NAME-node1 -n $NAME_SPACE
    kubectl apply -k $CHAIN_NAME-node2 -n $NAME_SPACE
    kubectl apply -k $CHAIN_NAME-node3 -n $NAME_SPACE
    kubectl apply -k $CHAIN_NAME-node4 -n $NAME_SPACE
fi

if [ $CHIAN_TYPE == "raft" ]
then
    echo "apply raft chain: 3 consensus and 1 readonly"
    kubectl apply -k $CHAIN_NAME-node0 -n $NAME_SPACE
    kubectl apply -k $CHAIN_NAME-node1 -n $NAME_SPACE
    kubectl apply -k $CHAIN_NAME-node2 -n $NAME_SPACE
    kubectl apply -k $CHAIN_NAME-node3 -n $NAME_SPACE
fi
