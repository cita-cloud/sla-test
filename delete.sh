#!/bin/bash
kubectl delete -f $CHAIN_NAME-node0/yamls/ -n $NAME_SPACE
kubectl delete -f $CHAIN_NAME-node1/yamls/ -n $NAME_SPACE
kubectl delete -f $CHAIN_NAME-node2/yamls/ -n $NAME_SPACE
kubectl delete -f $CHAIN_NAME-node3/yamls/ -n $NAME_SPACE
kubectl delete -f $CHAIN_NAME-node4/yamls/ -n $NAME_SPACE

