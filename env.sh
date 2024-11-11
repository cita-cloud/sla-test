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
unset EXPORTER_PATH

# 设置镜像仓库
# export DOCKER_REGISTRY=docker.io
# export DOCKER_REPO=citacloud
export DOCKER_REGISTRY=registry.devops.rivtower.com
export DOCKER_REPO=cita-cloud

# 设置链的版本
export RELEASE_VERSION=v6.7.4-beta1

# 设置链的共识类型和链的名称
# raft or overlord
export CHIAN_TYPE=overlord
export CHAIN_NAME=sla-$CHIAN_TYPE

# 设置基础环境的Storage Class和PVC access mode
export SC=cstor-csi-disk-ssd-sc
export PVC_MODE=ReadWriteOnce

# 设置要使用的NameSpace
export NAME_SPACE=cita-cloud-sla

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

# 设置export 到 kafka的相关设置
# 设置kafka-bridge的base url，例如：http://my-bridge-bridge-service.kafka.svc.cluster.local:8080
export EXPORTER_PATH=
