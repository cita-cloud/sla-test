import base64

from kubernetes import client, config
from minio import Minio


class Bucket(object):
    client = None

    def __new__(cls, *args, **kwargs):
        if not cls.client:
            cls.client = object.__new__(cls)
        return cls.client

    def __init__(self, service, access_key, secret_key, secure=False):
        self.service = service
        self.client = Minio(service, access_key=access_key, secret_key=secret_key, secure=secure)

    def exists_bucket(self, bucket_name):
        """
        判断桶是否存在
        :param bucket_name: 桶名称
        :return:
        """
        return self.client.bucket_exists(bucket_name=bucket_name)

    def remove_bucket(self, bucket_name):
        """
        删除桶
        :param bucket_name:
        :return:
        """
        try:
            objects = self.client.list_objects(bucket_name, recursive=True)
            for obj in objects:
                self.client.remove_object(bucket_name, obj.object_name)
            # remove bucket
            self.client.remove_bucket(bucket_name=bucket_name)
        except Exception as e:
            raise Exception(e)


class BucketConfig(object):
    def __init__(self, name, endpoint, minio_secret_name, minio_secret_namespace):
        self.name = name
        self.endpoint = endpoint
        self.minio_secret_name = minio_secret_name
        self.minio_secret_namespace = minio_secret_namespace
        # k8s
        config.load_kube_config()
        self.core_api = client.CoreV1Api()

    @property
    def access_key(self):
        try:
            secret_data = self.core_api.read_namespaced_secret(name=self.minio_secret_name,
                                                               namespace=self.minio_secret_namespace).data
            return base64.b64decode(secret_data["username"]).decode("utf-8")
        except Exception as e:
            raise e

    @property
    def secret_key(self):
        try:
            secret_data = self.core_api.read_namespaced_secret(name=self.minio_secret_name,
                                                               namespace=self.minio_secret_namespace).data
            return base64.b64decode(secret_data["password"]).decode("utf-8")
        except Exception as e:
            raise e


if __name__ == '__main__':
    pass
