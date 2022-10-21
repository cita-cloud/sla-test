# See the License for the specific language governing permissions and
# limitations under the License.

from kubernetes import client, config
from tenacity import retry, stop_after_attempt, wait_fixed, after_log

@retry(stop=stop_after_attempt(30), wait=wait_fixed(10))
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
        raise Exception("status not complete")
    return resource.get('status').get('status')