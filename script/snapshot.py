#!/usr/bin/env python3
import argparse

from kubernetes import client, config

from logger import logger
from util import wait_job_complete, get_env


class Snapshot(object):
    def __init__(self, name, namespace):
        config.load_kube_config()
        self.api = client.CustomObjectsApi()
        self.name = name
        self.namespace = namespace
        self.created = False

    def create(self, chain, node, block_height,
               deploy_method="cloud-config",
               storage_class="nas-client-provisioner",
               image="registry.devops.rivtower.com/cita-cloud/cita-node-job:latest",
               pull_policy="Always",
               ttl=30,
               pod_affinity_flag=True):
        resource_body = {
            "apiVersion": "citacloud.rivtower.com/v1",
            "kind": "Snapshot",
            "metadata": {"name": self.name},
            "spec": {
                "chain": chain,
                "node": node,
                "blockHeight": block_height,
                "deployMethod": deploy_method,
                "storageClass": storage_class,
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
            plural="snapshots",
            body=resource_body,
            _request_timeout=30,
        )
        self.created = True

    def wait_job_complete(self):
        return wait_job_complete("snapshots", self.name, self.namespace)

    def delete(self):
        self.api.delete_namespaced_custom_object(
            group="citacloud.rivtower.com",
            version="v1",
            name=self.name,
            namespace=self.namespace,
            plural="snapshots",
            body=client.V1DeleteOptions(),
            _request_timeout=30,
        )


if __name__ == '__main__':
    chain_name, namespace, sc, docker_registry, docker_repo = get_env()

    parser = argparse.ArgumentParser(description='Perform snapshot for chain node')
    parser.add_argument('--node_domain', '-n', help="the node's domain name", default='node4',
                        type=str)
    parser.add_argument('--block_height', '-b', help='block height number', required=True, type=int)
    parser.add_argument('--tag', '-t', help="cita node job image tag", default="v0.0.3", type=str)
    parser.add_argument('--pull_policy', '-p', help="image pull policy", default="Always", type=str,
                        choices=['Always', 'IfNotPresent'])
    args = parser.parse_args()

    snapshot = Snapshot(name="{}-snapshot".format(chain_name), namespace=namespace)
    try:
        # create snapshot job
        node = "{}-{}".format(chain_name, args.node_domain)
        logger.info(
            "create snapshot job -> [chain: {}, node: {}, block height: {}]...".format(chain_name, node,
                                                                                       args.block_height))
        snapshot.create(chain=chain_name,
                        node=node,
                        storage_class=sc,
                        block_height=args.block_height,
                        image="{}/{}/cita-node-job:{}".format(docker_registry, docker_repo, args.tag),
                        pull_policy=args.pull_policy)
        status = snapshot.wait_job_complete()
        if status == "Failed":
            raise Exception("snapshot exec failed")
        logger.info("the snapshot job has been completed")
    except Exception as e:
        logger.exception(e)
        exit(30)
