#!/usr/bin/env python
from __future__ import absolute_import

import json
import os
import os.path
import pkg_resources
import subprocess
import sys
from backports import tempfile

from ansible.module_utils._text import to_bytes

import click
import m9dicts
import yaml

from .model import PowoPlugin


# needed if powo launched from a virtualenv so that ansible-galaxy can be found
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
@click.option('--extra-vars', multiple=True,
              help='ansible extra vars')
@click.pass_context
def run(ctx, config, verbosity, extra_vars, args=None):
    os.chdir('/')
    configuration = {}
    configuration['extra_vars'] = m9dicts.make()
    for i in extra_vars:
        configuration['extra_vars'].update(json.loads(i))
    ctx.obj = {}
    ctx.obj['configuration'] = configuration


@run.command()
@click.option('--playbook', '-p', 'playbook_name', default=None,
              help='playbook to launch')
@click.option('--ask-become-pass', '-w', is_flag=True, default=False,
              help='ask for sudo password on command-line')
@click.pass_context
def update(ctx, playbook_name, ask_become_pass, **kwargs):
    extra_vars = ctx.obj['configuration']['extra_vars']
    # load default ansible options
    # parser = CLI.base_parser(connect_opts=True, meta_opts=True, runas_opts=True,
    #                          subset_opts=True, check_opts=True,
    #                          inventory_opts=True, runtask_opts=True,
    #                          vault_opts=True, fork_opts=True,
    #                          module_opts=True)
    # options = parser.parse_args(['--connection', 'local'])[0]
    # variable_manager = VariableManager()
    # loader = DataLoader()

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
        galaxy_command = lookup_ansible_script('ansible-galaxy')
        command_args = [galaxy_command[0]]
        command_env = dict(os.environ)
        command_env.update(galaxy_command[1])
        params = ['install', '--roles-path', galaxy_path]
        params.extend(galaxy_roles)

        command_args.extend(params)
        subprocess.check_call(command_args, env=command_env)

    passwords = dict()
    if ask_become_pass:
        sudo_pass = click.prompt('Please provide sudo password',
                                 hide_input=True)
        extra_vars['ansible_become_pass'] =\
            to_bytes(sudo_pass)

    plugin = plugins[0]
    playbooks = plugin.playbooks
    playbook_path = None
    if playbook_name is not None:
        for path in playbooks:
            if os.path.basename(path) == playbook_name:
                playbook_path = path
                break
        if playbook_path == None:
            raise Exception('playbook %s not found' % (playbook_name,))
    else:
        playbook_path = playbooks[0]
    if plugin.on_run is not None:
        plugin.on_run(ctx, extra_vars)

    command = lookup_ansible_script('ansible-playbook')
    for key, value in command[1].items():
        os.putenv(key, value)

    ansible_playbook_args = []
    ansible_playbook_args.append(command[0])
    ansible_playbook_args.extend(['-i', 'localhost,'])
    ansible_playbook_args.extend(['--connection', 'local'])
    if extra_vars is not None:
        ansible_playbook_args.extend([
            '-e',
            json.dumps(extra_vars)
        ])
    ansible_playbook_args.append(playbook_path)
    ansible_playbook_args.append('-v')

    with tempfile.TemporaryDirectory() as tempdir:
        ansible_config = os.path.join(tempdir, 'ansible.cfg')
        with open(ansible_config, 'w') as stream:
            configuration_content = """
[defaults]
roles_path = {roles_path}
hash_behaviour = merge
stdout_callback = skippy

            """.format(roles_path=':'.join(roles_path))
            stream.write(configuration_content)

        ansible_env = dict(os.environ)
        ansible_env['ANSIBLE_CONFIG'] = ansible_config
        ansible_env.update(command[1])

        subprocess.check_call(ansible_playbook_args, env=ansible_env)


def lookup_ansible_script(script):
    found_script = None
    environment = {}
    # we consider it as a marker for a pex environment
    if len(sys.path) > 0 and sys.path[0].endswith('/.bootstrap'):
        import ansible
        ansible_pkg = ansible.__path__[0]
        parent = os.path.dirname(ansible_pkg)
        # in pex env, scripts can be found in EGG-INFO/scripts directory
        egg_info_script = os.path.join(parent, 'EGG-INFO', 'scripts', script)
        if os.path.exists(egg_info_script):
            found_script = sys.argv[0]
            environment['PEX_SCRIPT'] = script
        else:
            print('Command "%s" not found in pex' % (script))
    if found_script == None:
        print('Using default command "%s"' % (script))
        found_script = script
    return (found_script, environment)


plugins = load_plugins()
for plugin in plugins:
    if plugin.decorate_update:
        plugin.decorate_update(update)


import pprint
