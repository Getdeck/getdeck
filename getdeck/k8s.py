import logging
import re
from typing import Callable, Any, Tuple, List

from getdeck.configuration import ClientConfiguration

logger = logging.getLogger("deck")


def k8s_create_or_patch(
    config: ClientConfiguration, obj, namespace: str, **kwargs
) -> None:
    from kubernetes.client.rest import ApiException

    api = k8s_select_api(config, obj)
    try:
        res = k8s_call_api(api, "create", obj, namespace, **kwargs)
        logger.debug(
            f"Kubernetes: {k8s_describe_object(obj)} created with uid={res.metadata.uid}"
        )
    except ApiException as e:
        if e.reason != "Conflict":
            raise
        try:
            res = k8s_call_api(api, "patch", obj, namespace, **kwargs)
            logger.debug(
                f"Kubernetes: {k8s_describe_object(obj)} patched with uid={res.metadata.uid}"
            )
        except ApiException as e:
            if e.reason != "Unprocessable Entity":
                logger.error(f"Error installing object: {e.reason}")
                raise
            try:
                # try again
                logger.debug(
                    f"Kubernetes: replacing {k8s_describe_object(obj)} "
                    f"failed. Attempting deletion and recreation."
                )
                res = k8s_call_api(api, "delete", obj, namespace, **kwargs)
                logger.debug(f"Kubernetes: {k8s_describe_object(obj)} deleted")
                res = k8s_call_api(api, "create", obj, namespace, **kwargs)
                logger.debug(
                    f"Kubernetes: {k8s_describe_object(obj)} created with uid={res.metadata.uid}"
                )
            except Exception as ex:
                logger.error(
                    f"Kubernetes: failure updating {k8s_describe_object(obj)}: {ex}"
                )
                raise RuntimeError(ex)
        except ValueError as e:
            logger.warning(
                f"Error installing object: {e}. This is probably caused by a skew in the Kubernetes version."
            )
    except ValueError as e:
        logger.warning(
            f"Error installing object: {e}. This is probably caused by a skew in the Kubernetes version."
        )


def k8s_delete_object(config: ClientConfiguration, obj, namespace, **kwargs) -> bool:
    from kubernetes.client.rest import ApiException

    api = k8s_select_api(config, obj)
    try:
        k8s_call_api(api, "delete", obj, namespace, **kwargs)
        logger.debug(f"Kubernetes: {k8s_describe_object(obj)} deleted")
        return True
    except ApiException as e:
        if e.reason == "Not Found":
            logger.debug(f"Kubernetes: {k8s_describe_object(obj)} does not exist")
            return False
        else:
            logger.error(f"Kubernetes: deleting {k8s_describe_object(obj)} failed: {e}")
            raise RuntimeError(e)


def k8s_select_api(config: ClientConfiguration, obj) -> Callable:
    group, _, version = obj["apiVersion"].partition("/")
    if version == "":
        version = group
        group = "core"
    group = "".join(
        part.capitalize() for part in group.rsplit(".k8s.io", 1)[0].split(".")
    )
    version = version.capitalize()

    api = f"{group}{version}Api"
    logger.debug(f"Selecting api {api}")
    k8s_api = config.get_k8s_api(api)
    if k8s_api is None:
        raise ValueError(f"Kubernetes API {api} not available")
    return k8s_api


def k8s_call_api(api, action, obj, namespace: str, **args) -> Any:
    kind = convert_camel_2_snake(obj["kind"])
    try:
        namespace = obj["metadata"]["namespace"]
    except KeyError:
        # take the namespace passed as installation target
        pass
    _func = f"{action}_{kind}"
    if hasattr(api, _func):
        function = getattr(api, _func)
    else:
        _func = f"{action}_namespaced_{kind}"
        function = getattr(api, _func)
        args["namespace"] = namespace
    if "create" not in _func:
        args["name"] = obj["metadata"]["name"]
    if "delete" in _func:
        from kubernetes.client.models.v1_delete_options import V1DeleteOptions

        obj = V1DeleteOptions()
    return function(body=obj, **args)


def k8s_describe_object(obj: dict) -> str:
    return f"{obj['kind']} '{obj['metadata']['name']}'"


def convert_camel_2_snake(_string) -> str:
    _string = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", _string)
    _string = re.sub("([a-z0-9])([A-Z])", r"\1_\2", _string).lower()
    return _string


def get_ingress_display(
    config: ClientConfiguration, namespace: str
) -> List[Tuple[str, str]]:
    result = []
    ingresss = config.K8S_NETWORKING_API.list_namespaced_ingress(namespace)
    for ingress in ingresss.items:
        for rule in ingress.spec.rules:
            _host = rule.host
            for path in rule.http.paths:
                result.append((_host, path.path))
    return result
