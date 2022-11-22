# See the License for the specific language governing permissions and
# limitations under the License.
import os
import logging

from kubernetes import client, config
from tenacity import retry, stop_after_attempt, wait_fixed, after_log

from logger import logger


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
    )
    if not resource.get('status'):
        raise Exception("no status")
    if resource.get('status').get('status') == 'Active':
        raise Exception("the job's status is still Active")
    return resource.get('status').get('status')


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
