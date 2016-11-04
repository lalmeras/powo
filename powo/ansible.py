#!/usr/bin/env python
from __future__ import absolute_import

import os
import os.path
import pkg_resources
import sys

from ansible import constants as C
from ansible.cli import CLI
from ansible.cli.galaxy import GalaxyCLI
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.plugins.callback import CallbackBase
from ansible.utils.unicode import to_bytes
from ansible import utils
from ansible.executor.task_queue_manager import TaskQueueManager

import click
import yaml

from .model import PowoPlugin


# needed if powo launched from a virtualenv so that ansible-galaxy can be found
display = utils.display.Display()
old_os_path = os.environ.get('PATH', '')
os.environ['PATH'] = os.path.dirname(os.path.abspath(__file__)) \
    + os.pathsep + old_os_path
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_plugins():
    plugins = []
    for ep in pkg_resources.iter_entry_points(group='powo_plugin'):
        value = ep.load()()
        if isinstance(value, PowoPlugin):
            plugins.append(value)
    return plugins


@click.group()
@click.option('--config', '-c',
              type=click.Path(exists=False, resolve_path=True),
              default=os.path.expanduser('~') + '/.powo/config.yml',
              help='path to custom configuration file')
@click.option('--quiet', '-q', 'verbosity',
              flag_value=0, default=False)
@click.option('--verbose', '-v', 'verbosity',
              flag_value=4, default=False)
@click.pass_context
def run(ctx, config, verbosity, args=None):
    os.chdir('/')
    if verbosity is None:
        verbosity = 2
    display.verbosity = verbosity
    configuration = {
        'vars': ['~/.powo/vars/config.yml']
    }
    try:
        with open(config, 'r') as stream:
            configuration.update(yaml.load(stream))
    except:
        print('File %s not found' % (config, ))
    configuration['vars'] = \
        [os.path.normpath(os.path.join(os.path.dirname(config),
                                       os.path.expanduser(path)))
         for path in configuration['vars']]
    ctx.obj = {}
    ctx.obj['configuration'] = configuration


@run.command()
@click.option('--ask-become-pass', '-w', is_flag=True, default=False,
              help='ask for sudo password on command-line')
@click.pass_context
def update(ctx, ask_become_pass, **kwargs):
    # load default ansible options
    parser = CLI.base_parser(connect_opts=True, meta_opts=True, runas_opts=True,
                             subset_opts=True, check_opts=True,
                             inventory_opts=True, runtask_opts=True,
                             vault_opts=True, fork_opts=True,
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
        params = ['ansible-galaxy', 'install', '--roles-path', galaxy_path]
        params.extend(galaxy_roles)
        cli = GalaxyCLI(params)
        # despite params is a CLI instance parameter
        # argv must be overriden
        argv_orig = sys.argv
        try:
            sys.argv = params
            cli.parse()
            cli.run()
        finally:
            sys.argv = argv_orig
    C.DEFAULT_ROLES_PATH = roles_path
    C.DEFAULT_HASH_BEHAVIOUR = 'merge'

    passwords = dict()
    if ask_become_pass:
        sudo_pass = click.prompt('Please provide sudo password',
                                 hide_input=True)
        passwords['become_pass'] = to_bytes(sudo_pass)

    # create inventory and pass to var manager
    inventory = Inventory(loader=loader,
                          variable_manager=variable_manager,
                          host_list=['localhost'])
    variable_manager.set_inventory(inventory)

    plugin = plugins[0]
    playbooks = plugin.playbooks
    playbook_path = playbooks[0]
    playbook = loader.load_from_file(playbook_path)[0]
    playbook['vars_files'].extend(ctx.obj['configuration']['vars'])
    loader.set_basedir(os.path.dirname(playbook_path))
    # plugin can modify some vars before execution
    pre_play = Play().load(playbook,
                           variable_manager=variable_manager,
                           loader=loader)
    if plugin.on_run is not None:
        plugin.on_run(ctx, pre_play, variable_manager, loader)
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
                  passwords=passwords,
                  stdout_callback='skippy'
        )
        tqm.run(play)
    finally:
        if tqm is not None:
            tqm.cleanup()


plugins = load_plugins()
for plugin in plugins:
    if plugin.decorate_update:
        plugin.decorate_update(update)


import pprint


class CallbackModule(CallbackBase):
    def on_any(self, *args, **kwargs):
        pass

    def runner_on_failed(self, host, res, ignore_errors=False):
        pprint.pprint(res)

    def runner_on_ok(self, host, res):
        pprint.pprint(res)

    def runner_on_error(self, host, msg):
        pprint.pprint(msg)

    def runner_on_skipped(self, host, item=None):
        pprint.pprint(item)

    def runner_on_unreachable(self, host, res):
        pass

    def runner_on_no_hosts(self):
        pass

    def runner_on_async_poll(self, host, res, jid, clock):
        pass

    def runner_on_async_ok(self, host, res, jid):
        pass

    def runner_on_async_failed(self, host, res, jid):
        pass

    def playbook_on_start(self):
        pass

    def playbook_on_notify(self, host, handler):
        pass

    def playbook_on_no_hosts_matched(self):
        pass

    def playbook_on_no_hosts_remaining(self):
        pass

    def playbook_on_task_start(self, name, is_conditional):
        print name
        pass

    def playbook_on_vars_prompt(self, varname, private=True, prompt=True,
                                encrypt=None, confirm=False, salt_size=None,
                                salt=None, default=None):
        pass

    def playbook_on_setup(self):
        pass

    def playbook_on_import_for_host(self, host, imported_file):
        pass

    def playbook_on_not_import_for_hosts(self, host, missing_file):
        pass

    def playbook_on_play_start(self, pattern):
        pass

    def playbook_on_stats(self, stats):
        pass
