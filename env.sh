#!/bin/bash

# 设置镜像仓库
# export DOCKER_REGISTRY=docker.io
# export DOCKER_REPO=citacloud
export DOCKER_REGISTRY=registry.devops.rivtower.com
export DOCKER_REPO=cita-cloud

# 设置链的版本
export RELEASE_VERSION=v6.6.4

# 设置链的类型和名称
# export CHIAN_TYPE=raft
export CHIAN_TYPE=overlord
export CHAIN_NAME=sla-$CHIAN_TYPE

# 设置基础环境的Storage Class
export SC=nas-client-provisioner

# 设置要使用的NameSpace
export NAME_SPACE=cita-cloud-sla

# 设置jager agent endpoint，如果不使用链路追踪功能则不设置该变量
export JAEGER_AGENT_ENDPOINT=jaeger.tracing.svc:6831
