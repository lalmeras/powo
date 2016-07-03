# -*- coding: utf-8 -*-


class PowoPlugin(object):
    def __init__(self, roles_path=None, playbooks=None, galaxy_roles=None):
        self.roles_path = roles_path
        self.playbooks = playbooks
        self.galaxy_roles = galaxy_roles
