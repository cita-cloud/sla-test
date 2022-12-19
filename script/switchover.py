#!/usr/bin/env python3
import argparse

from kubernetes import client, config

from util import wait_job_complete, logger, get_env


class Switchover(object):
    def __init__(self, name, namespace):
        config.load_kube_config()
        self.api = client.CustomObjectsApi()
        self.name = name
        self.namespace = namespace
        self.created = False

    def create(self, chain, source_node, dest_node,
               image="registry.devops.rivtower.com/cita-cloud/cita-node-job:latest",
               pull_policy="Always",
               ttl=30):
        resource_body = {
            "apiVersion": "citacloud.rivtower.com/v1",
            "kind": "Switchover",
            "metadata": {"name": self.name},
            "spec": {
                "chain": chain,
                "sourceNode": source_node,
                "destNode": dest_node,
                "pullPolicy": pull_policy,
                "image": image,
                "ttlSecondsAfterFinished": ttl
            },
        }

        # create a cluster scoped resource
        self.api.create_namespaced_custom_object(
            group="citacloud.rivtower.com",
            version="v1",
            namespace=self.namespace,
            plural="switchovers",
            body=resource_body,
            _request_timeout=30,
        )
        self.created = True

    def delete(self):
        self.api.delete_namespaced_custom_object(
            group="citacloud.rivtower.com",
            version="v1",
            name=self.name,
            namespace=self.namespace,
            plural="switchovers",
            body=client.V1DeleteOptions(),
            _request_timeout=30,
        )

    def wait_job_complete(self):
        return wait_job_complete("switchovers", self.name, self.namespace)


if __name__ == '__main__':
    chain_name, namespace, _, docker_registry, docker_repo = get_env()

    parser = argparse.ArgumentParser(description='Perform switch for two chain nodes')
    parser.add_argument('--source_node_domain', '-s', help="the source node's domain name", required=True, type=str)
    parser.add_argument('--dest_node_domain', '-d', help="the dest node's domain name", required=True, type=str)
    parser.add_argument('--tag', '-t', help="cita node job image tag", default="v0.0.3", type=str)
    parser.add_argument('--pull_policy', '-p', help="image pull policy", default="Always", type=str,
                        choices=['Always', 'IfNotPresent'])
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
                  dest_node=dest_node,
                  image="{}/{}/cita-node-job:{}".format(docker_registry, docker_repo, args.tag),
                  pull_policy=args.pull_policy)
        status = sw.wait_job_complete()
        if status == "Failed":
            raise Exception("switchover exec failed")
        logger.info("the switchover job has been completed")
    except Exception as e:
        logger.exception(e)
        exit(10)
