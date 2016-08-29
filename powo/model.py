# -*- coding: utf-8 -*-


class PowoPlugin(object):
    def __init__(self, roles_path=None, playbooks=None, galaxy_roles=None,
                 on_run=None, decorate_update=None):
        self.roles_path = roles_path
        self.playbooks = playbooks
        self.galaxy_roles = galaxy_roles
        self.on_run = on_run
        self.decorate_update = decorate_update
