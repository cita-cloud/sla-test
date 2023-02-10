#!/bin/bash
export DOCKER_REGISTRY=registry.devops.rivtower.com
export DOCKER_REPO=cita-cloud

# 设置链的版本
export RELEASE_VERSION=latest

# 设置链的类型和名称
# export CHIAN_TYPE=raft
export CHIAN_TYPE=overlord
export CHAIN_NAME=sla-$CHIAN_TYPE

# 设置基础环境的Storage Class
export SC=local-path

export NAME_SPACE=cita-cloud-sla

