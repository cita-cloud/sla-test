import argparse
import os
import sys

from kubernetes import client, config

from bucket import BucketConfig
from contants import BACKUP_REPO_SECRET_KEY, MINIO_CREDENTIALS_SECRET_ACCESS_KEY, MINIO_CREDENTIALS_SECRET_SECRET_KEY, \
    LOCAL, S3, LOCAL_WITH_EXIST_PVC

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import logger
from utils.util import wait_new_job_complete, get_env_for_v2


class RestoreConfig(object):
    def __init__(self,
                 backup,
                 storage_class,
                 backend_type,
                 pvc="integration-test-pvc",
                 mount_path="/bk/node_backup",
                 backup_repo_secret="backup-repo",):
        self.backup = backup
        self.storage_class = storage_class
        self.backend_type = backend_type
        self.pvc = pvc
        self.mount_path = mount_path
        self.backup_repo_secret = backup_repo_secret


class Restore(object):
    def __init__(self, name, namespace):
        config.load_kube_config()
        self.api = client.CustomObjectsApi()
        self.name = name
        self.namespace = namespace
        self.created = False

    def create(self,
               chain,
               node,
               deploy_method="cloud-config",
               restore_config: RestoreConfig = None,
               bucket_config: BucketConfig = None):
        if restore_config.backend_type == LOCAL:
            self.create_from_local(
                chain,
                node,
                restore_config.backup,
                deploy_method,
                restore_config.storage_class,
                backup_repo_name=restore_config.backup_repo_secret)
        elif restore_config.backend_type == LOCAL_WITH_EXIST_PVC:
            self.create_from_local_with_exist_pvc(chain,
                                                  node,
                                                  restore_config.backup,
                                                  deploy_method,
                                                  pvc=restore_config.pvc,
                                                  mount_path=restore_config.mount_path,
                                                  backup_repo_name=restore_config.backup_repo_secret)
        elif restore_config.backend_type == S3:
            self.create_form_s3(chain, node, restore_config.backup, deploy_method,
                                endpoint=bucket_config.endpoint,
                                bucket=bucket_config.name,
                                backup_repo_name=restore_config.backup_repo_secret,
                                minio_secret_name=bucket_config.minio_secret_name)
        else:
            raise Exception("mismatch restore backend type")

    def create_from_local(self,
                          chain,
                          node,
                          backup,
                          deploy_method="cloud-config",
                          storage_class="nas-client-provisioner",
                          backup_repo_name="backup-repo"):
        resource_body = {
            "apiVersion": "rivtower.com/v1cita",
            "kind": "Restore",
            "metadata": {"name": self.name},
            "spec": {
                "chain": chain,
                "node": node,
                "deployMethod": deploy_method,
                "backup": backup,
                "restoreMethod": {
                    "folder": {
                        "claimName": "datadir-{}-0".format(node)
                    }
                },
                "backend": {
                    "repoPasswordSecretRef": {
                        "name": backup_repo_name,
                        "key": BACKUP_REPO_SECRET_KEY,
                    },
                    "local": {
                        "mountPath": "/hello",
                        "storageClass": storage_class,
                    }
                }
            },
        }
        # create a cluster scoped resource
        self.api.create_namespaced_custom_object(
            group="rivtower.com",
            version="v1cita",
            namespace=self.namespace,
            plural="restores",
            body=resource_body,
        )
        self.created = True

    def create_from_local_with_exist_pvc(self,
                                         chain,
                                         node,
                                         backup,
                                         deploy_method="cloud-config",
                                         pvc="nas-client-provisioner",
                                         mount_path="/bk/node-backup",
                                         backup_repo_name="backup-repo"):
        resource_body = {
            "apiVersion": "rivtower.com/v1cita",
            "kind": "Restore",
            "metadata": {"name": self.name},
            "spec": {
                "chain": chain,
                "node": node,
                "deployMethod": deploy_method,
                "backup": backup,
                "restoreMethod": {
                    "folder": {
                        "claimName": "datadir-{}-0".format(node)
                    }
                },
                "backend": {
                    "repoPasswordSecretRef": {
                        "name": backup_repo_name,
                        "key": BACKUP_REPO_SECRET_KEY,
                    },
                    "local": {
                        "mountPath": mount_path,
                        "pvc": pvc,
                    }
                }
            },
        }
        # create a cluster scoped resource
        self.api.create_namespaced_custom_object(
            group="rivtower.com",
            version="v1cita",
            namespace=self.namespace,
            plural="restores",
            body=resource_body,
        )
        self.created = True

    def create_form_s3(self,
                       chain,
                       node,
                       backup,
                       deploy_method="cloud-config",
                       endpoint="minio.zhujq:9000",
                       bucket="k8up-full",
                       backup_repo_name="backup-repo",
                       minio_secret_name="minio-credentials"):
        resource_body = {
            "apiVersion": "rivtower.com/v1cita",
            "kind": "Restore",
            "metadata": {"name": self.name},
            "spec": {
                "chain": chain,
                "node": node,
                "deployMethod": deploy_method,
                "backup": backup,
                "restoreMethod": {
                    "folder": {
                        "claimName": "datadir-{}-0".format(node)
                    }
                },
                "backend": {
                    "repoPasswordSecretRef": {
                        "name": backup_repo_name,
                        "key": BACKUP_REPO_SECRET_KEY,
                    },
                    "s3": {
                        "endpoint": "http://" + endpoint,
                        "bucket": bucket,
                        "accessKeyIDSecretRef": {
                            "name": minio_secret_name,
                            "key": MINIO_CREDENTIALS_SECRET_ACCESS_KEY
                        },
                        "secretAccessKeySecretRef": {
                            "name": minio_secret_name,
                            "key": MINIO_CREDENTIALS_SECRET_SECRET_KEY,
                        },
                    }
                }
            },
        }
        # create a cluster scoped resource
        self.api.create_namespaced_custom_object(
            group="rivtower.com",
            version="v1cita",
            namespace=self.namespace,
            plural="restores",
            body=resource_body,
        )
        self.created = True

    def wait_job_complete(self):
        return wait_new_job_complete("restores", self.name, self.namespace)

    def delete(self):
        self.api.delete_namespaced_custom_object(
            group="rivtower.com",
            version="v1cita",
            name=self.name,
            namespace=self.namespace,
            plural="restores",
            body=client.V1DeleteOptions(),
        )

    def status(self):
        pass


if __name__ == '__main__':
    chain_name, namespace, sc = get_env_for_v2()

    parser = argparse.ArgumentParser(description='Perform restore for chain node')
    parser.add_argument('--node_domain', '-n',
                        help="the node's domain name",
                        required=True,
                        type=str)
    parser.add_argument('--backup_name',
                        help="the name of backup",
                        required=True,
                        type=str)
    parser.add_argument('--backend_type',
                        help="the type of backend [local/local-with-pvc/s3]",
                        required=True,
                        default="local",
                        choices=[LOCAL, LOCAL_WITH_EXIST_PVC, S3],
                        type=str)
    parser.add_argument('--pvc',
                        help="the pvc name if your backend type is local-exist-pvc",
                        required=False,
                        type=str)
    parser.add_argument('--mount_path',
                        help="the mount path if your backend type is local-exist-pvc",
                        required=False,
                        default="/hello",
                        type=str)
    parser.add_argument('--endpoint',
                        help="the endpoint of object storage if your backend type is s3",
                        required=False,
                        type=str)
    parser.add_argument('--bucket_name',
                        help="the bucket name of object storage if your backend type is s3",
                        required=False,
                        type=str)
    parser.add_argument('--backup_repo_secret',
                        help="the backup repo secret for restic",
                        required=False,
                        default="backup-repo",
                        type=str)
    parser.add_argument('--minio_secret',
                        help="the minio secret for object storage",
                        required=False,
                        default="minio-credentials",
                        type=str)
    args = parser.parse_args()

    restore = Restore(name="{}-restore".format(chain_name), namespace=namespace)
    try:
        node = "{}-{}".format(chain_name, args.node_domain)
        logger.info(
            "create restore job -> [chain: {}, node: {}, restore from: {}]...".format(chain_name, node,
                                                                                      args.backend_type))

        bucket_cfg = BucketConfig(name=args.bucket_name,
                                  endpoint=args.endpoint,
                                  minio_secret_name=args.minio_secret,
                                  minio_secret_namespace=namespace) if args.backend_type == S3 else None

        restore_cfg = RestoreConfig(backup=args.backup_name,
                                    storage_class=sc,
                                    backend_type=args.backend_type,
                                    pvc=args.pvc,
                                    mount_path=args.mount_path,
                                    backup_repo_secret=args.backup_repo_secret)

        restore.create(chain=chain_name,
                       node=node,
                       restore_config=restore_cfg,
                       bucket_config=bucket_cfg)

        status = restore.wait_job_complete()
        if status == "Failed":
            raise Exception("restore exec failed")
        logger.info("the restore job for {} has been completed".format(args.backend_type))
    except Exception as e:
        logger.exception(e)
        exit(10)
