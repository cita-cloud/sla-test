#!/bin/bash

# 创建NameSpace
kubectl create ns cita-cloud-sla

kubectl apply -f sla-cita-node0/ -n cita-cloud-sla
kubectl apply -f sla-cita-node1/ -n cita-cloud-sla
kubectl apply -f sla-cita-node2/ -n cita-cloud-sla
kubectl apply -f sla-cita-node3/ -n cita-cloud-sla

