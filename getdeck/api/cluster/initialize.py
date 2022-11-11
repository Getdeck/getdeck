import logging
from getdeck.configuration import ClientConfiguration
from getdeck.provider.abstract import AbstractProvider

from getdeck.provider.types import ProviderType


logger = logging.getLogger("deck")


def initialize(
    provider_type: ProviderType,
    config: ClientConfiguration,
    name: str,
    native_config: dict = None,
) -> AbstractProvider:
    from getdeck.provider.factory import cluster_factory

    try:
        cluster = cluster_factory.get(
            provider_type=provider_type,
            config=config,
            name=name,
            native_config=native_config,
        )
        return cluster
    except Exception as e:
        logger.error(e)
        raise e
