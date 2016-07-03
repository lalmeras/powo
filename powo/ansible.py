#!/usr/bin/env python
from __future__ import absolute_import

import os.path
import pkg_resources

from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible import constants as C

import plumbum

from .model import PowoPlugin


def run():
    Options = namedtuple('Options', ['connection', 'module_path',
                                     'forks',
                                     'become', 'become_method', 'become_user',
                                     'check'])
    # initialize needed objects
    variable_manager = VariableManager()
    loader = DataLoader()
    plugins = load_plugins()
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

    options = Options(connection='local',
                      module_path=None,
                      forks=100,
                      become=None, become_method=None, become_user=None,
                      check=False)
    passwords = dict(vault_pass='secret')

    # create inventory and pass to var manager
    inventory = Inventory(loader=loader,
                          variable_manager=variable_manager,
                          host_list=['localhost'])
    variable_manager.set_inventory(inventory)

    playbooks = [playbook_path
                 for plugin in plugins
                 for playbook_path in plugin.playbooks
                 if plugin.playbooks is not None]
    playbook_path = playbooks[0]
    playbook = loader.load_from_file(playbook_path)[0]
    loader.set_basedir(os.path.dirname(playbook_path))
    # # create play with tasks
    # play_source = dict(
    #         name="Ansible Play",
    #         hosts='localhost',
    #         gather_facts='no',
    #         tasks=[]
    #         # tasks=[
    #         #    dict(action=dict(module='shell', args='ls'),
    #         #         register='shell_out'),
    #         #    dict(action=dict(module='debug',
    #         #                     args=dict(msg='{{shell_out.stdout}}')))
    #         # ]
    #     )
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
