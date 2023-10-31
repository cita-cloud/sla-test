#!/bin/bash

kubectl delete -f sla-cita-node0/ -n cita-cloud-sla
kubectl delete -f sla-cita-node1/ -n cita-cloud-sla
kubectl delete -f sla-cita-node2/ -n cita-cloud-sla
kubectl delete -f sla-cita-node3/ -n cita-cloud-sla
