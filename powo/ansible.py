#!/usr/bin/env python
from __future__ import absolute_import

import os.path
import pkg_resources
import sys

from ansible.cli import CLI
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.utils.unicode import to_bytes
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible import constants as C

import click
import plumbum

from .model import PowoPlugin


@click.command()
@click.option('--ask-become-pass', '-w', is_flag=True, default=False)
def run(ask_become_pass, args=None):
    # load default ansible options
    parser = CLI.base_parser(connect_opts=True, meta_opts=True, runas_opts=True,
                             subset_opts=True, check_opts=True, inventory_opts=True,
                             runtask_opts=True, vault_opts=True, fork_opts=True,
                             module_opts=True)
    options = parser.parse_args(['--connection', 'local'])[0]
    variable_manager = VariableManager()
    loader = DataLoader()

    # load powo plugins
    plugins = load_plugins()

    # build roles_path with provided roles path and galaxy folder
    roles_path = [p.roles_path for p in plugins if p.roles_path is not None]
    galaxy_roles = [galaxy_role
                    for plugin in plugins
                    for galaxy_role in plugin.galaxy_roles
                    if plugin.galaxy_roles is not None]
    galaxy_path = '/tmp/powo-galaxy'
    if not os.path.exists(galaxy_path):
        os.makedirs(galaxy_path)
    if len(galaxy_roles) > 0:
        roles_path.insert(0, galaxy_path)
        plumbum.local['ansible-galaxy']('install',
                                        '--roles-path', galaxy_path,
                                        *galaxy_roles)
    C.DEFAULT_ROLES_PATH = roles_path

    passwords = dict()
    if ask_become_pass:
        sudo_pass = click.prompt('Please provide sudo password', hide_input=True)
        passwords['become_pass'] = to_bytes(sudo_pass)

    # create inventory and pass to var manager
    inventory = Inventory(loader=loader,
                          variable_manager=variable_manager,
                          host_list=['localhost'])
    variable_manager.extra_vars = {'ansible_python_interpreter': sys.executable}
    variable_manager.set_inventory(inventory)

    playbooks = [playbook_path
                 for plugin in plugins
                 for playbook_path in plugin.playbooks
                 if plugin.playbooks is not None]
    playbook_path = playbooks[0]
    playbook = loader.load_from_file(playbook_path)[0]
    loader.set_basedir(os.path.dirname(playbook_path))
    play = Play().load(playbook,
                       variable_manager=variable_manager,
                       loader=loader)

    # actually run it
    tqm = None
    try:
        tqm = TaskQueueManager(
                  inventory=inventory,
                  variable_manager=variable_manager,
                  loader=loader,
                  options=options,
                  passwords=passwords)
        tqm.run(play)
    finally:
        if tqm is not None:
            tqm.cleanup()


def load_plugins():
    plugins = []
    for ep in pkg_resources.iter_entry_points(group='powo_plugin'):
        value = ep.load()()
        if isinstance(value, PowoPlugin):
            plugins.append(value)
    return plugins
