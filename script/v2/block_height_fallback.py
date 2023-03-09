#!/usr/bin/env python3
import argparse
import os
import sys

from kubernetes import client, config

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import logger
from utils.util import wait_new_job_complete, get_env_for_v2


class BlockHeightFallback(object):
    def __init__(self, name, namespace):
        config.load_kube_config()
        self.custom_api = client.CustomObjectsApi()
        self.name = name
        self.namespace = namespace
        self.created = False

    def create(self,
               chain,
               node,
               block_height,
               deploy_method="cloud-config"):
        resource_body = {
            "apiVersion": "rivtower.com/v1cita",
            "kind": "BlockHeightFallback",
            "metadata": {"name": self.name},
            "spec": {
                "chain": chain,
                "node": node,
                "deployMethod": deploy_method,
                "blockHeight": block_height
            },
        }
        # create a cluster scoped resource
        self.custom_api.create_namespaced_custom_object(
            group="rivtower.com",
            version="v1cita",
            namespace=self.namespace,
            plural="blockheightfallbacks",
            body=resource_body,
        )
        self.created = True

    def wait_job_complete(self):
        return wait_new_job_complete("blockheightfallbacks", self.name, self.namespace)

    def delete(self):
        self.custom_api.delete_namespaced_custom_object(
            group="rivtower.com",
            version="v1cita",
            name=self.name,
            namespace=self.namespace,
            plural="blockheightfallbacks",
            body=client.V1DeleteOptions(),
        )


if __name__ == '__main__':
    chain_name, namespace, sc = get_env_for_v2()

    parser = argparse.ArgumentParser(description='Perform block height fallback for chain node')
    parser.add_argument('--block_height', '-b', help='block height number', required=True, type=int)
    parser.add_argument('--node_domain', '-n', help="the node's domain name", required=True, type=str)
    args = parser.parse_args()

    bhf = BlockHeightFallback(name="{}-bhf".format(chain_name), namespace=namespace)
    try:
        node = "{}-{}".format(chain_name, args.node_domain)
        logger.info(
            "create fallback job for [chain: {}, node: {}, expected block height: {}]...".format(chain_name, node,
                                                                                                 args.block_height))
        bhf.create(chain=chain_name,
                   node=node,
                   block_height=args.block_height)
        status = bhf.wait_job_complete()
        if status == "Failed":
            raise Exception("block height fallback exec failed")
        logger.info("the fallback job has been completed")
    except Exception as e:
        logger.exception(e)
        exit(20)
