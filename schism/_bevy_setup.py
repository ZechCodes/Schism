"""Registers bevy hooks needed by Schism.

Bevy 3.x uses a hook-based system for customizing instance creation. Schism's Service class uses
a __bevy_constructor__ classmethod to control whether a local instance or a remote bridge facade
is created. This module registers hooks on the global registry so that any container created from
it will support the Schism protocols:

- CREATE_INSTANCE hook: delegates to __bevy_constructor__ when present on a type
- HANDLE_UNSUPPORTED_DEPENDENCY hook: loads ApplicationConfig from schism.config files"""
from pathlib import Path

from bevy.hooks import Hook, HookDecorator
from tramp.optionals import Optional


_setup_done = False


@HookDecorator(Hook.CREATE_INSTANCE)
def _bevy_constructor_hook(container, dependency_type):
    """Checks if a type defines __bevy_constructor__ and delegates instance creation to it."""
    if isinstance(dependency_type, type) and hasattr(dependency_type, "__bevy_constructor__"):
        return Optional.Some(dependency_type.__bevy_constructor__())
    return Optional.Nothing()


@HookDecorator(Hook.HANDLE_UNSUPPORTED_DEPENDENCY)
def _application_config_hook(container, dependency_type):
    """Loads ApplicationConfig from schism.config.{yaml,yml,json,toml} when requested via bevy."""
    from schism.configs import ApplicationConfig
    if dependency_type is not ApplicationConfig:
        return Optional.Nothing()

    return Optional.Some(_load_application_config())


def _load_application_config():
    """Searches the working directory for a schism.config file and loads it into an ApplicationConfig."""
    from schism.configs import ApplicationConfig
    from nubby.builtins.loaders import JsonLoader

    loader_types = [JsonLoader]
    try:
        from nubby.builtins.loaders import YamlLoader
        loader_types.append(YamlLoader)
    except ImportError:
        pass
    try:
        from nubby.builtins.loaders import TomlLoader
        loader_types.append(TomlLoader)
    except ImportError:
        pass

    for loader_cls in loader_types:
        for ext in loader_cls.extensions:
            path = Path.cwd() / f"schism.config.{ext}"
            if path.exists():
                loader = loader_cls(path)
                data = loader.load()
                return ApplicationConfig(**data)

    raise FileNotFoundError(
        "No schism.config file found in the working directory. "
        "Expected schism.config.yaml, schism.config.json, or schism.config.toml."
    )


def setup_bevy_hooks():
    """Register Schism's bevy hooks on the global registry. Safe to call multiple times."""
    global _setup_done
    if _setup_done:
        return
    _setup_done = True
    _bevy_constructor_hook.register_hook()
    _application_config_hook.register_hook()
