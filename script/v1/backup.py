#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring
import argparse
import os
import sys

from kubernetes import client, config

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import logger
from utils.util import wait_job_complete, get_env


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
            _request_timeout=30,
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
            _request_timeout=30,
        )


if __name__ == "__main__":
    chain_name, namespace, sc, docker_registry, docker_repo = get_env()

    parser = argparse.ArgumentParser(description='Perform backup for chain node')
    parser.add_argument('--node_domain', '-n', help="the node's domain name", required=True, type=str)
    parser.add_argument('--tag', '-t', help="cita node job image tag", default="v0.0.7", type=str)
    parser.add_argument('--pull_policy', '-p', help="image pull policy", default="Always", type=str,
                        choices=['Always', 'IfNotPresent'])
    args = parser.parse_args()

    backup = Backup(name="{}-backup".format(chain_name), namespace=namespace)
    try:
        # create backup job
        node = "{}-{}".format(chain_name, args.node_domain)
        logger.info("create backup job -> [chain: {}, node: {}]...".format(chain_name, node))
        backup.create(chain=chain_name,
                      node=node,
                      storage_class=sc,
                      image="{}/{}/cita-node-job:{}".format(docker_registry, docker_repo, args.tag),
                      pull_policy=args.pull_policy)
        status = backup.wait_job_complete()
        if status == "Failed":
            raise Exception("backup exec failed")
        logger.info("the backup job has been completed")
    except Exception as e:
        logger.exception(e)
        exit(10)
