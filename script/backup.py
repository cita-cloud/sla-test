#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring

import os
from pprint import pprint
from kubernetes import client, config
from util import wait_job_complete

class Backup(object):
    def __init__(self, name, namespace):
        config.load_kube_config()
        self.api = client.CustomObjectsApi()
        self.name = name
        self.namespace = namespace
        self.created = False

    def create(self, chain, node, storage_class, image,
               deploy_method="cloud-config",
               action="StopAndStart",
               pull_policy="IfNotPresent",
               ttl=300,
               pod_affinity_flag=True):
        resource_body = {
            "apiVersion": "citacloud.rivtower.com/v1",
            "kind": "Backup",
            "metadata": {"name": self.name},
            "spec": {
                "chain": chain,
                "node": node,
                "deployMethod": deploy_method,
                "storageClass": storage_class,
                "action": action,
                "pullPolicy": pull_policy,
                "image": image,
                "ttlSecondsAfterFinished": ttl,
                "podAffinityFlag": pod_affinity_flag,
            },
        }
        # create a cluster scoped resource
        self.api.create_namespaced_custom_object(
            group="citacloud.rivtower.com",
            version="v1",
            namespace=self.namespace,
            plural="backups",
            body=resource_body,
        )
        self.created = True

    def wait_job_complete(self):
        return wait_job_complete("backups", self.name, self.namespace)

    def delete(self):
        self.api.delete_namespaced_custom_object(
            group="citacloud.rivtower.com",
            version="v1",
            name=self.name,
            namespace=self.namespace,
            plural="backups",
            body=client.V1DeleteOptions(),
        )


if __name__ == "__main__":
    chain_name = os.getenv("CHAIN_NAME")
    namespace = os.getenv("NAME_SPACE")
    sc = os.getenv("SC")
    docker_registry = os.getenv("DOCKER_REGISTRY")
    docker_repo = os.getenv("DOCKER_REPO")

    backup = Backup(name = "{}-backup".format(chain_name), namespace = namespace)
    try:
        # create backup job
        backup.create(chain = chain_name,
                      node = "{}-node4".format(chain_name),
                      storage_class = sc,
                      image = "{}/{}/cita-node-job:v0.0.2".format(docker_registry, docker_repo))
        status = backup.wait_job_complete()
        if status == "Failed":
            raise Exception("backup exec failed")
    except Exception as e:
        pprint(e)
        exit(10)
