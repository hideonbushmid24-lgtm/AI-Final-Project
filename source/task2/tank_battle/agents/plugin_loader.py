"""Load external Tank Battle agents from Python files."""

import hashlib
import importlib.util
import sys

from pathlib import Path

from .base_agent import BaseAgent


class PluginLoadError(RuntimeError):
    """Raised when an external agent plugin cannot be loaded."""


class PluginLoader:
    """
    Dynamically load an external agent class from a .py file.

    External plugins must define a class inheriting BaseAgent.
    The class must implement select_action(state).
    """

    @staticmethod
    def load_agent(
        file_path,
        class_name: str,
        **constructor_kwargs,
    ) -> BaseAgent:
        """
        Load and instantiate an external agent.

        Example:
            agent = PluginLoader.load_agent(
                "plugins/my_agent.py",
                "MyAgent",
            )
        """

        path = Path(file_path).expanduser().resolve()

        if not path.exists():
            raise PluginLoadError(
                f"Plugin file does not exist: {path}"
            )

        if not path.is_file():
            raise PluginLoadError(
                f"Plugin path is not a file: {path}"
            )

        if path.suffix.lower() != ".py":
            raise PluginLoadError(
                "Plugin must be a Python (.py) file."
            )

        if not class_name or not isinstance(class_name, str):
            raise PluginLoadError(
                "A valid plugin class name is required."
            )

        # Use a stable module name derived from the file path
        # and modification time.
        try:
            stat = path.stat()
            identity = f"{path}:{stat.st_mtime_ns}:{stat.st_size}"
            digest = hashlib.sha256(
                identity.encode("utf-8")
            ).hexdigest()[:16]

            module_name = f"tank_battle_external_{digest}"

            spec = importlib.util.spec_from_file_location(
                module_name,
                path,
            )

            if spec is None or spec.loader is None:
                raise PluginLoadError(
                    "Could not create a module specification."
                )

            module = importlib.util.module_from_spec(spec)

            # Register before execution so imports within the
            # module can resolve its module identity.
            sys.modules[module_name] = module

            try:
                spec.loader.exec_module(module)
            except Exception:
                sys.modules.pop(module_name, None)
                raise

        except PluginLoadError:
            raise
        except Exception as exc:
            raise PluginLoadError(
                f"Failed to import plugin {path.name}: {exc}"
            ) from exc

        agent_class = getattr(module, class_name, None)

        if agent_class is None:
            raise PluginLoadError(
                f"Class '{class_name}' was not found in {path.name}."
            )

        if not isinstance(agent_class, type):
            raise PluginLoadError(
                f"'{class_name}' must be a class."
            )

        if not issubclass(agent_class, BaseAgent):
            raise PluginLoadError(
                f"'{class_name}' must inherit from BaseAgent."
            )

        try:
            agent = agent_class(**constructor_kwargs)
        except Exception as exc:
            raise PluginLoadError(
                f"Could not instantiate '{class_name}': {exc}"
            ) from exc

        if not isinstance(agent, BaseAgent):
            raise PluginLoadError(
                "Plugin instance does not implement BaseAgent."
            )

        return agent