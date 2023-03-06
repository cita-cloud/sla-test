import argparse
import base64
import os
import sys

import kubernetes.client.exceptions
from kubernetes import client, config

from bucket import Bucket, BucketConfig
from contants import FULL_BACKUP, STATE_BACKUP, LOCAL, S3, LOCAL_WITH_EXIST_PVC, BACKUP_REPO_SECRET_KEY, \
    MINIO_CREDENTIALS_SECRET_ACCESS_KEY, MINIO_CREDENTIALS_SECRET_SECRET_KEY

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import logger
from utils.util import wait_new_job_complete, get_env_for_v2


class BackupConfig(object):
    def __init__(self,
                 backup_type,
                 backend_type,
                 block_height=10,
                 storage_class="nas-client-provisioner",
                 pvc="integration-test-pvc",
                 mount_path="/bk/node_backup",
                 backup_repo_secret="backup-repo",
                 secret_namespace="cita"):
        self.backup_type = backup_type
        self.backend_type = backend_type
        self.block_height = block_height
        self.storage_class = storage_class
        self.pvc = pvc
        self.mount_path = mount_path
        self.backup_repo_secret = backup_repo_secret
        self.secret_namespace = secret_namespace

        # k8s
        config.load_kube_config()
        self.core_api = client.CoreV1Api()

    @property
    def backup_repo_password(self):
        try:
            secret_data = self.core_api.read_namespaced_secret(name=self.backup_repo_secret,
                                                               namespace=self.secret_namespace).data
            return str(base64.b64decode(secret_data["password"]))
        except Exception as ex:
            raise ex


class Backup(object):

    def __init__(self, name, namespace):
        config.load_kube_config()
        self.custom_api = client.CustomObjectsApi()
        self.core_api = client.CoreV1Api()
        self.name = name
        self.namespace = namespace
        # crate or not
        self.created = False

    def check_secret(self, name, namespace):
        try:
            self.core_api.read_namespaced_secret(name, namespace)
            logger.debug("check secret ok, the secret {}/{} already exist".format(namespace, name))
        except kubernetes.client.exceptions.ApiException:
            raise Exception("the secret is not exist: {}/{}".format(namespace, name))

    def create(self,
               chain,
               node,
               deploy_method="cloud-config",
               backup_cfg: BackupConfig = None,
               bucket_cfg: BucketConfig = None):
        self.check_secret(name=backup_cfg.backup_repo_secret, namespace=backup_cfg.secret_namespace)
        if bucket_cfg is not None:
            self.check_secret(name=bucket_cfg.minio_secret_name, namespace=bucket_cfg.minio_secret_namespace)

        if backup_cfg.backend_type == LOCAL:
            self._local_backup(chain,
                               node,
                               backup_type=backup_cfg.backup_type,
                               deploy_method=deploy_method,
                               storage_class=backup_cfg.storage_class,
                               block_height=backup_cfg.block_height,
                               backup_repo_name=backup_cfg.backup_repo_secret)
        elif backup_cfg.backend_type == LOCAL_WITH_EXIST_PVC:
            self._local_backup_with_exist_pvc(chain,
                                              node,
                                              backup_type=backup_cfg.backup_type,
                                              deploy_method=deploy_method,
                                              pvc=backup_cfg.pvc,
                                              mount_path=backup_cfg.mount_path,
                                              block_height=backup_cfg.block_height,
                                              backup_repo_name=backup_cfg.backup_repo_secret)
        elif backup_cfg.backend_type == S3:
            minio_obj = Bucket(service=bucket_cfg.endpoint,
                               access_key=bucket_cfg.access_key,
                               secret_key=bucket_cfg.secret_key)
            # remove if onj exist
            if minio_obj.exists_bucket(bucket_cfg.name):
                logger.debug("bucket {} exist, remove it...".format(bucket_cfg.name))
                minio_obj.remove_bucket(bucket_cfg.name)
            self._s3_backup(chain,
                            node,
                            backup_type=backup_cfg.backup_type,
                            deploy_method=deploy_method,
                            endpoint=bucket_cfg.endpoint,
                            bucket=bucket_cfg.name,
                            block_height=backup_cfg.block_height,
                            backup_repo_name=backup_cfg.backup_repo_secret,
                            minio_secret_name=bucket_cfg.minio_secret_name)

    def _local_backup(self,
                      chain,
                      node,
                      backup_type=FULL_BACKUP,
                      deploy_method="cloud-config",
                      storage_class="nas-client-provisioner",
                      block_height=10,
                      backup_repo_name="backup-repo"):
        """
        创建本地备份
        :param chain:
        :param node:
        :param backup_type:
        :param deploy_method:
        :param storage_class:
        :param block_height: 块高，当backup_type为状态备份时，需要指定该值
        :param backup_repo_name: backup_repo_name secret
        :return:
        """
        # resource_body = None
        if backup_type == FULL_BACKUP:
            resource_body = {
                "apiVersion": "rivtower.com/v1cita",
                "kind": "Backup",
                "metadata": {"name": self.name},
                "spec": {
                    "chain": chain,
                    "node": node,
                    "deployMethod": deploy_method,
                    "dataType": {
                        "full": {
                            "includePaths": ["data", "chain_data"]
                        }
                    },
                    "failedJobsHistoryLimit": 2,
                    "successfulJobsHistoryLimit": 2,
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
        elif backup_type == STATE_BACKUP:
            resource_body = {
                "apiVersion": "rivtower.com/v1cita",
                "kind": "Backup",
                "metadata": {"name": self.name},
                "spec": {
                    "chain": chain,
                    "node": node,
                    "deployMethod": deploy_method,
                    "dataType": {
                        "state": {
                            "blockHeight": block_height
                        }
                    },
                    "failedJobsHistoryLimit": 2,
                    "successfulJobsHistoryLimit": 2,
                    "backend": {
                        "repoPasswordSecretRef": {
                            "name": backup_repo_name,
                            "key": BACKUP_REPO_SECRET_KEY,
                        },
                        "local": {
                            "mountPath": "/hello",
                            "storageClass": storage_class,
                            "size": "10Gi"
                        }
                    }
                },
            }
        else:
            raise Exception("mismatched backup type")
        # create a cluster scoped resource
        self.custom_api.create_namespaced_custom_object(
            group="rivtower.com",
            version="v1cita",
            namespace=self.namespace,
            plural="backups",
            body=resource_body,
        )
        self.created = True

    def _local_backup_with_exist_pvc(self,
                                     chain,
                                     node,
                                     backup_type=FULL_BACKUP,
                                     deploy_method="cloud-config",
                                     pvc="nas-client-provisioner",
                                     mount_path="/bk/node-backup",
                                     block_height=10,
                                     backup_repo_name="backup-repo"):
        """
        创建本地备份(用户提供pvc)
        :param chain:
        :param node:
        :param backup_type:
        :param deploy_method:
        :param pvc: pvc name
        :param mount_path: 挂载点
        :param block_height: 块高,状态备份时使用
        :param backup_repo_name: backup_repo_name secret
        :return:
        """
        if backup_type == FULL_BACKUP:
            resource_body = {
                "apiVersion": "rivtower.com/v1cita",
                "kind": "Backup",
                "metadata": {"name": self.name},
                "spec": {
                    "chain": chain,
                    "node": node,
                    "deployMethod": deploy_method,
                    "dataType": {
                        "full": {
                            "includePaths": ["data", "chain_data"]
                        }
                    },
                    "failedJobsHistoryLimit": 2,
                    "successfulJobsHistoryLimit": 2,
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
        elif backup_type == STATE_BACKUP:
            resource_body = {
                "apiVersion": "rivtower.com/v1cita",
                "kind": "Backup",
                "metadata": {"name": self.name},
                "spec": {
                    "chain": chain,
                    "node": node,
                    "deployMethod": deploy_method,
                    "dataType": {
                        "state": {
                            "blockHeight": block_height
                        }
                    },
                    "failedJobsHistoryLimit": 2,
                    "successfulJobsHistoryLimit": 2,
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
        else:
            raise Exception("mismatched backup type")
        # create a cluster scoped resource
        self.custom_api.create_namespaced_custom_object(
            group="rivtower.com",
            version="v1cita",
            namespace=self.namespace,
            plural="backups",
            body=resource_body,
        )
        self.created = True

    def _s3_backup(self,
                   chain,
                   node,
                   backup_type=FULL_BACKUP,
                   deploy_method="cloud-config",
                   endpoint="minio.zhujq:9000",
                   bucket="k8up-full",
                   block_height=10,
                   backup_repo_name="backup-repo",
                   minio_secret_name="minio-credentials"):
        if backup_type == FULL_BACKUP:
            resource_body = {
                "apiVersion": "rivtower.com/v1cita",
                "kind": "Backup",
                "metadata": {"name": self.name},
                "spec": {
                    "chain": chain,
                    "node": node,
                    "deployMethod": deploy_method,
                    "dataType": {
                        "full": {
                            "includePaths": ["data", "chain_data"]
                        }
                    },
                    "failedJobsHistoryLimit": 3,
                    "successfulJobsHistoryLimit": 3,
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
        elif backup_type == STATE_BACKUP:
            resource_body = {
                "apiVersion": "rivtower.com/v1cita",
                "kind": "Backup",
                "metadata": {"name": self.name},
                "spec": {
                    "chain": chain,
                    "node": node,
                    "deployMethod": deploy_method,
                    "dataType": {
                        "state": {
                            "blockHeight": block_height
                        }
                    },
                    "failedJobsHistoryLimit": 3,
                    "successfulJobsHistoryLimit": 3,
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
        else:
            raise Exception("mismatched backup type")

        # create a cluster scoped resource
        self.custom_api.create_namespaced_custom_object(
            group="rivtower.com",
            version="v1cita",
            namespace=self.namespace,
            plural="backups",
            body=resource_body,
        )
        self.created = True

    def wait_job_complete(self):
        return wait_new_job_complete("backups", self.name, self.namespace)

    def delete(self):
        self.custom_api.delete_namespaced_custom_object(
            group="rivtower.com",
            version="v1cita",
            name=self.name,
            namespace=self.namespace,
            plural="backups",
            body=client.V1DeleteOptions(),
        )


if __name__ == '__main__':
    chain_name, namespace, sc = get_env_for_v2()

    parser = argparse.ArgumentParser(description='Perform backup for chain node')
    parser.add_argument('--node_domain', '-n',
                        help="the node's domain name",
                        required=True,
                        type=str)
    parser.add_argument('--backup_type',
                        help="the type of backup [full/state]",
                        required=True,
                        default="full",
                        choices=[FULL_BACKUP, STATE_BACKUP],
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
    parser.add_argument('--block_height',
                        help="the block height number when you want to execute state backup",
                        required=False,
                        type=int)
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

    backup = Backup(name="{}-backup".format(chain_name), namespace=namespace)
    try:
        # create backup job
        node = "{}-{}".format(chain_name, args.node_domain)
        logger.info("create backup job -> [chain: {}, node: {}]...".format(chain_name, node))

        backup_cfg = BackupConfig(backup_type=args.backup_type,
                                  backend_type=args.backend_type,
                                  # 快照至5#
                                  block_height=args.block_height,
                                  storage_class=sc,
                                  pvc=args.pvc,
                                  mount_path=args.mount_path,
                                  backup_repo_secret=args.backup_repo_secret,
                                  secret_namespace=namespace)
        bucket_cfg = BucketConfig(name=args.bucket_name,
                                  endpoint=args.endpoint,
                                  minio_secret_name=args.minio_secret,
                                  minio_secret_namespace=namespace) if args.backend_type == S3 else None

        backup.create(chain=chain_name,
                      node=node,
                      backup_cfg=backup_cfg,
                      bucket_cfg=bucket_cfg)
        status = backup.wait_job_complete()
        if status == "Failed":
            raise Exception("backup exec failed")
        logger.info("the backup job has been completed")
    except Exception as e:
        logger.exception(e)
        exit(10)
