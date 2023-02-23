#!/bin/bash

# 设置环境变量
source ./env.sh

if [ $CHIAN_TYPE == "overlord" ]
then
    echo "delete overlord chain: 4 consensus and 1 readonly"
    kubectl delete -f $CHAIN_NAME-node0/yamls/ -n $NAME_SPACE
    kubectl delete -f $CHAIN_NAME-node1/yamls/ -n $NAME_SPACE
    kubectl delete -f $CHAIN_NAME-node2/yamls/ -n $NAME_SPACE
    kubectl delete -f $CHAIN_NAME-node3/yamls/ -n $NAME_SPACE
    kubectl delete -f $CHAIN_NAME-node4/yamls/ -n $NAME_SPACE
fi

if [ $CHIAN_TYPE == "raft" ]
then
    echo "delete raft chain: 3 consensus and 1 readonly"
    kubectl delete -f $CHAIN_NAME-node0/yamls/ -n $NAME_SPACE
    kubectl delete -f $CHAIN_NAME-node1/yamls/ -n $NAME_SPACE
    kubectl delete -f $CHAIN_NAME-node2/yamls/ -n $NAME_SPACE
    kubectl delete -f $CHAIN_NAME-node3/yamls/ -n $NAME_SPACE
fi
