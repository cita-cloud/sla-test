#!/usr/bin/env python3
import argparse
import os
import sys

from kubernetes import client, config

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import logger
from utils.util import wait_new_job_complete, get_env_for_v2


class Switchover(object):
    def __init__(self, name, namespace):
        config.load_kube_config()
        self.api = client.CustomObjectsApi()
        self.name = name
        self.namespace = namespace
        self.created = False

    def create(self,
               chain,
               source_node,
               dest_node,):
        resource_body = {
            "apiVersion": "rivtower.com/v1cita",
            "kind": "Switchover",
            "metadata": {"name": self.name},
            "spec": {
                "chain": chain,
                "sourceNode": source_node,
                "destNode": dest_node,
            },
        }

        # create a cluster scoped resource
        self.api.create_namespaced_custom_object(
            group="rivtower.com",
            version="v1cita",
            namespace=self.namespace,
            plural="switchovers",
            body=resource_body,
        )
        self.created = True

    def delete(self):
        self.api.delete_namespaced_custom_object(
            group="rivtower.com",
            version="v1cita",
            name=self.name,
            namespace=self.namespace,
            plural="switchovers",
            body=client.V1DeleteOptions(),
        )

    def wait_job_complete(self):
        return wait_new_job_complete("switchovers", self.name, self.namespace)


def check_node_account_switched(namespace, name, wanted_account_name):
    config.load_kube_config()
    apps_v1 = client.AppsV1Api()
    exist = False
    node_sts = apps_v1.read_namespaced_stateful_set(name=name, namespace=namespace)
    for volume in node_sts.spec.template.spec.volumes:
        if volume.config_map.name == wanted_account_name:
            exist = True
    return exist


if __name__ == '__main__':
    chain_name, namespace, sc = get_env_for_v2()

    parser = argparse.ArgumentParser(description='Perform switch for two chain nodes')
    parser.add_argument('--source_node_domain', '-s', help="the source node's domain name", required=True, type=str)
    parser.add_argument('--dest_node_domain', '-d', help="the dest node's domain name", required=True, type=str)
    args = parser.parse_args()

    sw = Switchover(name="{}-switchover".format(chain_name), namespace=namespace)
    try:
        source_node = "{}-{}".format(chain_name, args.source_node_domain)
        dest_node = "{}-{}".format(chain_name, args.dest_node_domain)
        logger.info(
            "create switchover job -> [chain: {}, source_node: {}, dest_node: {}]...".format(chain_name, source_node,
                                                                                             dest_node))
        sw.create(chain=chain_name,
                  source_node=source_node,
                  dest_node=dest_node)
        status = sw.wait_job_complete()
        if status == "Failed":
            raise Exception("switchover exec failed")
        logger.info("the switchover job has been completed")
    except Exception as e:
        logger.exception(e)
        exit(10)
