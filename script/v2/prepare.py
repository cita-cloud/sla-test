import argparse
import base64
import os
import sys

import kubernetes.client.exceptions
from kubernetes import client, config

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import logger
from utils.util import get_env_for_v2


def create_backup_secret(args):
    config.load_kube_config()
    core_api = client.CoreV1Api()

    _, namespace, _ = get_env_for_v2()
    name = args.name
    password = args.password
    try:
        core_api.read_namespaced_secret(name, namespace)
        logger.debug("the backup repo secret already exist")
    except kubernetes.client.exceptions.ApiException:
        logger.debug("create backup repo secret {}/{} ...".format(namespace, name))
        secret = client.V1Secret()
        secret.api_version = 'v1'
        data = {'password': str(base64.b64encode(password.encode(encoding="utf-8")), "utf-8")}
        secret.data = data
        secret.kind = 'Secret'
        secret.metadata = {"name": name}
        secret.type = 'Opaque'
        core_api.create_namespaced_secret(namespace, secret, pretty="true")
        logger.debug("create backup repo secret {}/{} successful".format(namespace, name))


def create_minio_credentials(args):
    config.load_kube_config()
    core_api = client.CoreV1Api()

    _, namespace, _ = get_env_for_v2()
    name = args.name
    access_key = args.access_key
    secret_key = args.secret_key

    try:
        core_api.read_namespaced_secret(name, namespace)
        logger.debug("the minio credentials secret already exist")
    except kubernetes.client.exceptions.ApiException:
        logger.debug("create minio credentials secret {}/{} ...".format(namespace, name))
        secret = client.V1Secret()
        secret.api_version = 'v1'
        data = {
            'username': str(base64.b64encode(access_key.encode(encoding="utf-8")), "utf-8"),
            'password': str(base64.b64encode(secret_key.encode(encoding="utf-8")), "utf-8"),
        }
        secret.data = data
        secret.kind = 'Secret'
        secret.metadata = {"name": name}
        secret.type = 'Opaque'
        core_api.create_namespaced_secret(namespace, secret, pretty="true")
        logger.debug("create minio credentials secret {}/{} successful".format(namespace, name))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Prepare Command')

    subparsers = parser.add_subparsers(help='sub-command help')

    # add subcommand create_backup_secret
    parser_a = subparsers.add_parser('create_backup_secret', help='create backup secret')
    parser_a.add_argument('--name',
                          help="the name of backup repo secret",
                          required=False,
                          default="backup-repo",
                          type=str)
    parser_a.add_argument('--password',
                          help="the password of backup repo secret",
                          required=False,
                          default="p@ssw0rd",
                          type=str)
    parser_a.set_defaults(func=create_backup_secret)

    # add subcommand create_minio_credentials
    parser_s = subparsers.add_parser('create_minio_credentials', help='create minio credentials')
    parser_s.add_argument('--name',
                          help="the name of minio credentials",
                          required=False,
                          default="minio-credentials",
                          type=str)
    parser_s.add_argument('--access_key',
                          help="the access key of minio credentials",
                          required=False,
                          default="minio",
                          type=str)
    parser_s.add_argument('--secret_key',
                          help="the secret ket of minio credentials",
                          required=False,
                          default="minio123",
                          type=str)
    parser_s.set_defaults(func=create_minio_credentials)

    args = parser.parse_args()

    args.func(args)
