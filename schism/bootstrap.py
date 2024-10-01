from typing import Generator

from bevy import inject, dependency
import os

from schism.configs import ServiceConfig, ServicesConfig


SCHISM_BOOTSTRAP_SERVICES_VAR = "SCHISM_SERVICES"


def launch():
    ...


@inject
def _get_bootstrap_services(config: ServicesConfig = dependency()) -> Generator[ServiceConfig, None, None]:
    services = os.getenv(SCHISM_BOOTSTRAP_SERVICES_VAR)
    if not services or not services.split(","):
        raise RuntimeError(f"No services are listed in the {SCHISM_BOOTSTRAP_SERVICES_VAR} environment variable.")

    service_imports = {s.strip() for s in services.split(",")}
    for service in config.services:
        if service in service_imports:
            yield service
