import importlib.util
import os
from typing import List, Dict, Any
from agents.base_agent import BaseAgent

class PluginManager:
    def __init__(self, plugins_dir: str = None):
        if plugins_dir is None:
            # Default to the plugins directory relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.plugins_dir = os.path.join(current_dir, 'plugins')
        else:
            self.plugins_dir = plugins_dir
        self.plugins = []  # list of plugin modules
        self.loaded_agents = []  # list of agent instances from plugins

    def load_plugins(self):
        """Load all plugins from the plugins directory."""
        if not os.path.exists(self.plugins_dir):
            print(f"Plugins directory not found: {self.plugins_dir}")
            return
        for filename in os.listdir(self.plugins_dir):
            if filename.endswith('.py') and filename not in ['__init__.py', 'manager.py']:
                plugin_name = filename[:-3]
                plugin_path = os.path.join(self.plugins_dir, filename)
                try:
                    spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    self.plugins.append(module)
                    print(f"Loaded plugin: {plugin_name}")
                except Exception as e:
                    print(f"Failed to load plugin {plugin_name}: {e}")

    def register_plugins(self, toolkit) -> List[BaseAgent]:
        """
        Call the register function of each plugin to get agents.
        Each plugin should have a register(toolkit) function that returns a list of BaseAgent instances.
        Returns a list of all agents from all plugins.
        """
        agents = []
        for plugin in self.plugins:
            if hasattr(plugin, 'register'):
                try:
                    plugin_agents = plugin.register(toolkit)
                    if isinstance(plugin_agents, list):
                        agents.extend(plugin_agents)
                        print(f"Plugin {plugin.__name__} registered {len(plugin_agents)} agents")
                    else:
                        print(f"Plugin {plugin.__name__} register function did not return a list")
                except Exception as e:
                    print(f"Error calling register for plugin {plugin.__name__}: {e}")
            else:
                print(f"Plugin {plugin.__name__} has no register function")
        self.loaded_agents = agents
        return agents