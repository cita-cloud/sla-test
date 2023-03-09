# See the License for the specific language governing permissions and
# limitations under the License.
import logging
import os

from kubernetes import client, config
from tenacity import retry, stop_after_attempt, wait_fixed, after_log
from utils.logger import logger


@retry(stop=stop_after_attempt(30), wait=wait_fixed(10), after=after_log(logger, logging.DEBUG))
def wait_job_complete(crd, cr_name, namespace):
    config.load_kube_config()
    api = client.CustomObjectsApi()
    resource = api.get_namespaced_custom_object(
        group="citacloud.rivtower.com",
        version="v1",
        name=cr_name,
        namespace=namespace,
        plural=crd,
        _request_timeout=30,
    )
    if not resource.get('status'):
        raise Exception("no status")
    if resource.get('status').get('status') == 'Active':
        raise Exception("the job's status is still Active")
    return resource.get('status').get('status')


@retry(stop=stop_after_attempt(60), wait=wait_fixed(3), after=after_log(logger, logging.DEBUG))
def wait_new_job_complete(crd, cr_name, namespace):
    """
    for k8-up operator status
    :param crd:
    :param cr_name:
    :param namespace:
    :return:
    """
    config.load_kube_config()
    api = client.CustomObjectsApi()
    resource = api.get_namespaced_custom_object(
        group="rivtower.com",
        version="v1cita",
        name=cr_name,
        namespace=namespace,
        plural=crd,
    )
    if not resource.get('status'):
        raise Exception("no status")
    complete_flag = False
    for condition in resource.get('status').get('conditions'):
        if condition.get('type') == 'Completed':
            return condition.get('reason')
    if not complete_flag:
        raise Exception("the job's status is still Active")


def get_env():
    chain_name = os.getenv("CHAIN_NAME")
    if chain_name is None:
        raise Exception("need set environment variable for CHAIN_NAME")
    namespace = os.getenv("NAME_SPACE")
    if namespace is None:
        raise Exception("need set environment variable for NAME_SPACE")
    sc = os.getenv("SC")
    if sc is None:
        raise Exception("need set environment variable for SC")
    docker_registry = os.getenv("DOCKER_REGISTRY")
    if docker_registry is None:
        raise Exception("need set environment variable for DOCKER_REGISTRY")
    docker_repo = os.getenv("DOCKER_REPO")
    if docker_repo is None:
        raise Exception("need set environment variable for DOCKER_REPO")
    return chain_name, namespace, sc, docker_registry, docker_repo


def get_env_for_v2():
    chain_name = os.getenv("CHAIN_NAME")
    if chain_name is None:
        raise Exception("need set environment variable for CHAIN_NAME")
    namespace = os.getenv("NAME_SPACE")
    if namespace is None:
        raise Exception("need set environment variable for NAME_SPACE")
    sc = os.getenv("SC")
    if sc is None:
        raise Exception("need set environment variable for SC")
    return chain_name, namespace, sc
