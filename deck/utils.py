import logging
import os
import subprocess
from typing import Union

from semantic_version import Version

from deck import configuration
from deck.configuration import ClientConfiguration
from deck.deckfile.file import Deckfile, DeckfileDeck, DeckfileHelmSource, DeckfileDirectorySource
from deck.provider.abstract import AbstractK8sProvider

logger = logging.getLogger("deck")


def sniff_protocol(ref: str):
    if ref.startswith("git"):
        return "git"
    return None


def read_deckfile_from_location(location: str, config: ClientConfiguration) -> Deckfile:
    protocol = sniff_protocol(location)
    if location == ".":
        # load default file from this location
        return config.deckfile_selector.get(
            os.path.join(os.getcwd(), configuration.DECKFILE_FILE)
        )
    elif protocol is None:
        # this is probably a file system location
        if os.path.isfile(location):
            logger.debug("Is file location")
            return config.deckfile_selector.get(location)


class CMDWrapper(object):
    base_command = None

    class CMDException(Exception):
        pass

    def __init__(self, debug_output=False):
        self._debug_output = debug_output

    def _execute(
        self, arguments, stdin: str = None, print_output: bool = False
    ) -> subprocess.Popen:
        cmd = [self.base_command] + arguments
        kwargs = self._get_kwargs()
        process = subprocess.Popen(cmd, **kwargs)
        if stdin:
            process.communicate(stdin)
        try:
            if print_output:
                for stdout_line in iter(process.stdout.readline, ""):
                    print(stdout_line, end="", flush=True)
            process.wait()
        except KeyboardInterrupt:
            try:
                process.terminate()
            except OSError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
        return process

    def _run(self, arguments) -> subprocess.CompletedProcess:
        cmd = [self.base_command] + arguments
        return subprocess.run(cmd, env=self._get_environment())

    def _get_kwargs(self):
        kwargs = {"env": self._get_environment(), "encoding": "utf-8"}
        if not self._debug_output:
            kwargs.update(
                {
                    "stdout": subprocess.PIPE,
                    "close_fds": True,
                    "stderr": subprocess.STDOUT,
                }
            )
        return kwargs

    def _get_environment(self):
        env = os.environ.copy()
        return env


def ensure_cluster(deckfile: Deckfile, config: ClientConfiguration, do_install=True) -> AbstractK8sProvider:
    cluster_config = deckfile.get_cluster()
    k8s_provider = cluster_config.get_provider(config)
    version = k8s_provider.version()

    try:
        if cluster_config.minVersion:
            if Version(cluster_config.minVersion) > version:
                logger.warning(f"{cluster_config.provider} is installed in version {version}, "
                               f"but minVersion is {cluster_config.minVersion}")
                if do_install:
                    k8s_provider.update()
        else:
            logger.info(f"{cluster_config.provider} is installed in version {version}")
    except FileNotFoundError as e:
        if do_install:
            logger.info(f"{cluster_config.provider} is not installed, going to install now")
            #  this K8s provider is not yet installed
            k8s_provider.install()
    return k8s_provider


def createOrUpdateOrReplace(obj, client=None, **kwargs):
    """invoke the K8s API to create or replace a kubernetes object.
        The first attempt is to create(insert) this object; when this is rejected because
        of an existing object with same name, we attempt to patch this existing object.
        As a last resort, if even the patch is rejected, we *delete* the existing object
        and recreate from scratch.
        @param obj: complete object specification, including API version and metadata.
        @param client: (optional) preconfigured client environment to use for invocation
        @param kwargs: (optional) further arguments to pass to the create/replace call
        @return: response object from Kubernetes API call
    """
    k8sApi = findK8sApi(obj, client)
    try:
        res = invokeApi(k8sApi, 'create', obj, **kwargs)
        logging.debug('K8s: %s created -> uid=%s', describe(obj), res.metadata.uid)
    except kubernetes.client.rest.ApiException as apiEx:
        if apiEx.reason != 'Conflict': raise
        try:
            # asking for forgiveness...
            res = invokeApi(k8sApi, 'patch', obj, **kwargs)
            logging.debug('K8s: %s PATCHED -> uid=%s', describe(obj), res.metadata.uid)
        except kubernetes.client.rest.ApiException as apiEx:
            if apiEx.reason != 'Unprocessable Entity': raise
            try:
                # second attempt... delete the existing object and re-insert
                logging.debug('K8s: replacing %s FAILED. Attempting deletion and recreation...', describe(obj))
                res = invokeApi(k8sApi, 'delete', obj, **kwargs)
                logging.debug('K8s: %s DELETED...', describe(obj))
                res = invokeApi(k8sApi, 'create', obj, **kwargs)
                logging.debug('K8s: %s CREATED -> uid=%s', describe(obj), res.metadata.uid)
            except Exception as ex:
                message = 'K8s: FAILURE updating %s. Exception: %s' % (describe(obj), ex)
                logging.error(message)
                raise RuntimeError(message)
    return res


def patchObject(obj, client=None, **kwargs):
    k8sApi = findK8sApi(obj, client)
    try:
        res = invokeApi(k8sApi, 'patch', obj, **kwargs)
        logging.debug('K8s: %s PATCHED -> uid=%s', describe(obj), res.metadata.uid)
        return res
    except kubernetes.client.rest.ApiException as apiEx:
        if apiEx.reason == 'Unprocessable Entity':
            message = 'K8s: patch for %s rejected. Exception: %s' % (describe(obj), apiEx)
            logging.error(message)
            raise RuntimeError(message)
        else:
            raise


def deleteObject(obj, client=None, **kwargs):
    k8sApi = findK8sApi(obj, client)
    try:
        res = invokeApi(k8sApi, 'delete', obj, **kwargs)
        logging.debug('K8s: %s DELETED. uid was: %s', describe(obj), res.details and res.details.uid or '?')
        return True
    except kubernetes.client.rest.ApiException as apiEx:
        if apiEx.reason == 'Not Found':
            logging.warning('K8s: %s does not exist (anymore).', describe(obj))
            return False
        else:
            message = 'K8s: deleting %s FAILED. Exception: %s' % (describe(obj), apiEx)
            logging.error(message)
            raise RuntimeError(message)



def findK8sApi(obj, client=None):
    ''' Investigate the object spec and lookup the corresponding API object
        @param client: (optional) preconfigured client environment to use for invocation
        @return: a client instance wired to the apriopriate API
    '''
    grp, _, ver = obj['apiVersion'].partition('/')
    if ver == '':
        ver = grp
        grp = 'core'
    # Strip 'k8s.io', camel-case-join dot separated parts. rbac.authorization.k8s.io -> RbacAuthorzation
    grp = ''.join(part.capitalize() for part in grp.rsplit('.k8s.io', 1)[0].split('.'))
    ver = ver.capitalize()

    k8sApi = '%s%sApi' % (grp, ver)
    return getattr(kubernetes.client, k8sApi)(client)


def invokeApi(k8sApi, action, obj, **args):
    ''' find a suitalbe function and perform the actual API invocation.
        @param k8sApi: client object for the invocation, wired to correct API version
        @param action: either 'create' (to inject a new objet) or 'replace','patch','delete'
        @param obj: the full object spec to be passed into the API invocation
        @param args: (optional) extraneous arguments to pass
        @return: response object from Kubernetes API call
    '''
    # transform ActionType from Yaml into action_type for swagger API
    kind = camel2snake(obj['kind'])
    # determine namespace to place the object in, supply default
    try: namespace = obj['metadata']['namespace']
    except: namespace = 'default'

    functionName = '%s_%s' %(action,kind)
    if hasattr(k8sApi, functionName):
        # namespace agnostic API
        function = getattr(k8sApi, functionName)
    else:
        functionName = '%s_namespaced_%s' %(action,kind)
        function = getattr(k8sApi, functionName)
        args['namespace'] = namespace
    if not 'create' in functionName:
        args['name'] = obj['metadata']['name']
    if 'delete' in functionName:
        from kubernetes.client.models.v1_delete_options import V1DeleteOptions
        obj = V1DeleteOptions()

    return function(body=obj, **args)


def describe(obj):
    return "%s '%s'" % (obj['kind'], obj['metadata']['name'])


def camel2snake(string):
    string = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', string)
    string = re.sub('([a-z0-9])([A-Z])', r'\1_\2', string).lower()
    return string