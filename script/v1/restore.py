#!/usr/bin/env python3
import argparse
import os
import sys

from kubernetes import client, config

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import logger
from utils.util import wait_job_complete, get_env


class Restore(object):
    def __init__(self, name, namespace):
        config.load_kube_config()
        self.api = client.CustomObjectsApi()
        self.name = name
        self.namespace = namespace
        self.created = False

    def create_for_backup(self, chain, node,
                          backup, image,
                          deploy_method="cloud-config",
                          action="StopAndStart",
                          pull_policy="IfNotPresent",
                          ttl=300,
                          pod_affinity_flag=True,
                          delete_consensus_data=False):
        resource_body = {
            "apiVersion": "citacloud.rivtower.com/v1",
            "kind": "Restore",
            "metadata": {"name": self.name},
            "spec": {
                "chain": chain,
                "node": node,
                "deployMethod": deploy_method,
                "backup": backup,
                "action": action,
                "pullPolicy": pull_policy,
                "image": image,
                "ttlSecondsAfterFinished": ttl,
                "podAffinityFlag": pod_affinity_flag,
                "deleteConsensusData": delete_consensus_data,
            },
        }
        # create a cluster scoped resource
        self.api.create_namespaced_custom_object(
            group="citacloud.rivtower.com",
            version="v1",
            namespace=self.namespace,
            plural="restores",
            body=resource_body,
        )
        self.created = True

    def create_for_snapshot(self, chain, node,
                            snapshot, image,
                            deploy_method="cloud-config",
                            action="StopAndStart",
                            pull_policy="IfNotPresent",
                            ttl=30,
                            pod_affinity_flag=True,
                            delete_consensus_data=False):
        resource_body = {
            "apiVersion": "citacloud.rivtower.com/v1",
            "kind": "Restore",
            "metadata": {"name": self.name},
            "spec": {
                "chain": chain,
                "node": node,
                "deployMethod": deploy_method,
                "snapshot": snapshot,
                "action": action,
                "pullPolicy": pull_policy,
                "image": image,
                "ttlSecondsAfterFinished": ttl,
                "podAffinityFlag": pod_affinity_flag,
                "deleteConsensusData": delete_consensus_data,
            },
        }
        # create a cluster scoped resource
        self.api.create_namespaced_custom_object(
            group="citacloud.rivtower.com",
            version="v1",
            namespace=self.namespace,
            plural="restores",
            body=resource_body,
            _request_timeout=30,
        )
        self.created = True

    def wait_job_complete(self):
        return wait_job_complete("restores", self.name, self.namespace)

    def delete(self):
        self.api.delete_namespaced_custom_object(
            group="citacloud.rivtower.com",
            version="v1",
            name=self.name,
            namespace=self.namespace,
            plural="restores",
            body=client.V1DeleteOptions(),
            _request_timeout=30,
        )


if __name__ == "__main__":
    chain_name, namespace, _, docker_registry, docker_repo = get_env()

    parser = argparse.ArgumentParser(description='Perform restore for chain node')
    parser.add_argument('--method', '-m', help='restore from', required=True, type=str,
                        choices=['backup', 'snapshot'])
    parser.add_argument('--node_domain', '-n', help="the node's domain name", required=True, type=str)
    parser.add_argument('--tag', '-t', help="cita node job image tag", default="v0.0.7", type=str)
    parser.add_argument('--pull_policy', '-p', help="image pull policy", default="Always", type=str,
                        choices=['Always', 'IfNotPresent'])
    parser.add_argument('--action', '-a', help="action fo restore", default="StopAndStart", type=str,
                        choices=['StopAndStart', 'Direct'])
    parser.add_argument('--delete_consensus_data', '-d', help="is need delete consensus data fo restore", action='store_true')
    args = parser.parse_args()

    restore = Restore(name="{}-restore".format(chain_name), namespace=namespace)
    try:
        node = "{}-{}".format(chain_name, args.node_domain)
        if args.method == "backup":
            # create restore job for backup
            logger.info(
                "create restore job -> [chain: {}, node: {}, restore from: {}]...".format(chain_name, node,
                                                                                          args.method))
            restore.create_for_backup(chain=chain_name,
                                      node=node,
                                      backup="{}-backup".format(chain_name),
                                      image="{}/{}/cita-node-job:{}".format(docker_registry, docker_repo, args.tag),
                                      pull_policy=args.pull_policy,
                                      action=args.action,
                                      delete_consensus_data=args.delete_consensus_data)
        elif args.method == "snapshot":
            # create restore job for snapshot
            logger.info("create restore job -> [chain: {}, node: {}, restore from: {}]...".format(chain_name, node,
                                                                                                  args.method))
            restore.create_for_snapshot(chain=chain_name,
                                        node=node,
                                        snapshot="{}-snapshot".format(chain_name),
                                        image="{}/{}/cita-node-job:{}".format(docker_registry, docker_repo, args.tag),
                                        pull_policy=args.pull_policy,
                                        action=args.action,
                                        delete_consensus_data=args.delete_consensus_data)
        else:
            raise Exception("invalid restore method")
        status = restore.wait_job_complete()
        if status == "Failed":
            raise Exception("restore exec failed")
        logger.info("the restore job for {} has been completed".format(args.method))
    except Exception as e:
        logger.exception(e)
        exit(10)
