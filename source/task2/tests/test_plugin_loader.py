import pytest

from tank_battle.constants import Action
from tank_battle.scenario import create_default_scenario

from tank_battle.agents import (
    BaseAgent,
    PluginLoader,
    PluginLoadError,
)


VALID_PLUGIN = '''
from tank_battle.agents.base_agent import BaseAgent
from tank_battle.constants import Action

class ExampleExternalAgent(BaseAgent):

    name = "Example External Agent"

    def select_action(self, state):
        return Action.STAY
'''


def test_plugin_loader_loads_external_agent(tmp_path):
    plugin_file = tmp_path / "example_agent.py"
    plugin_file.write_text(
        VALID_PLUGIN,
        encoding="utf-8",
    )

    agent = PluginLoader.load_agent(
        plugin_file,
        "ExampleExternalAgent",
    )

    assert isinstance(agent, BaseAgent)
    assert agent.name == "Example External Agent"

    action = agent.get_action(create_default_scenario())

    assert action == Action.STAY


def test_plugin_loader_rejects_missing_file(tmp_path):
    missing_file = tmp_path / "missing_agent.py"

    with pytest.raises(PluginLoadError):
        PluginLoader.load_agent(
            missing_file,
            "MissingAgent",
        )


def test_plugin_loader_rejects_missing_class(tmp_path):
    plugin_file = tmp_path / "wrong_name.py"
    plugin_file.write_text(
        "VALUE = 123\n",
        encoding="utf-8",
    )

    with pytest.raises(PluginLoadError):
        PluginLoader.load_agent(
            plugin_file,
            "MissingAgent",
        )


def test_plugin_loader_rejects_class_without_base_agent(tmp_path):
    plugin_file = tmp_path / "invalid_agent.py"

    plugin_file.write_text(
        '''
class InvalidAgent:
    def select_action(self, state):
        return "STAY"
''',
        encoding="utf-8",
    )

    with pytest.raises(PluginLoadError):
        PluginLoader.load_agent(
            plugin_file,
            "InvalidAgent",
        )


def test_plugin_loader_rejects_invalid_extension(tmp_path):
    plugin_file = tmp_path / "agent.txt"
    plugin_file.write_text(
        "print('not a plugin')",
        encoding="utf-8",
    )

    with pytest.raises(PluginLoadError):
        PluginLoader.load_agent(
            plugin_file,
            "ExampleAgent",
        )


def test_plugin_loader_forwards_constructor_arguments(tmp_path):
    plugin_file = tmp_path / "configurable_agent.py"

    plugin_file.write_text(
        '''
from tank_battle.agents.base_agent import BaseAgent
from tank_battle.constants import Action

class ConfigurableAgent(BaseAgent):

    def __init__(self, selected_action="STAY"):
        self.selected_action = selected_action

    def select_action(self, state):
        return self.selected_action
''',
        encoding="utf-8",
    )

    agent = PluginLoader.load_agent(
        plugin_file,
        "ConfigurableAgent",
        selected_action="FIRE",
    )

    action = agent.get_action(create_default_scenario())

    assert action == Action.FIRE


def test_plugin_loader_rejects_syntax_error(tmp_path):
    plugin_file = tmp_path / "broken_agent.py"
    plugin_file.write_text(
        "class BrokenAgent(\n",
        encoding="utf-8",
    )

    with pytest.raises(PluginLoadError):
        PluginLoader.load_agent(
            plugin_file,
            "BrokenAgent",
        )