import re
import os
from collections import defaultdict

from fabric.api import cd, sudo, puts
from fabric.contrib import files
from fabric.contrib.files import exists

from fabdeploy.containers import conf
from fabdeploy.task import Task
from fabdeploy.users import list_users
from fabdeploy.files import read_file
from fabdeploy.utils import run_as_sudo, get_home_dir, split_lines


__all__ = ['push_key', 'list_authorized_files', 'list_keys']


class PushKey(Task):
    @conf
    def pub_key_file(self):
        pub_key_file = os.path.expanduser(self.conf.pub_key_file)
        return pub_key_file

    @run_as_sudo
    def do(self):
        with open(self.conf.pub_key_file, 'rt') as f:
            ssh_key = f.read()

        home_dir = get_home_dir(self.conf.user)
        with cd(home_dir):
            sudo('mkdir --parents .ssh')
            files.append('.ssh/authorized_keys', ssh_key, use_sudo=True)
            sudo('chown --recursive %(user)s:%(user)s .ssh' % self.conf)

push_key = PushKey()


class SshManagementTask(Task):
    def before_do(self):
        super(SshManagementTask, self).before_do()
        self.conf.setdefault('exclude_users', [])


class ListAuthorizedFiles(SshManagementTask):
    @run_as_sudo
    def get_authorized_files(self, exclude_users=None):
        users = list_users.get_users(exclude_users=exclude_users)

        authorized_files = []
        for user in users:
            dirpath = get_home_dir(user)
            authorized_file = '%s/.ssh/authorized_keys' % dirpath
            if exists(authorized_file, use_sudo=True):
                authorized_files.append((user, authorized_file))
        return authorized_files

    def do(self):
        authorized_files = self.get_authorized_files(
            exclude_users=self.conf.exclude_users)
        for user, authorized_file in authorized_files:
            puts(authorized_file)

list_authorized_files = ListAuthorizedFiles()


class ListKeys(SshManagementTask):
    @run_as_sudo
    def get_keys(self):
        authorized_files = list_authorized_files.get_authorized_files()

        keys = defaultdict(list)
        for user, authorized_file in authorized_files:
            content = read_file(authorized_file, use_sudo=True)
            for key in split_lines(content):
                if key.startswith('#'):
                    continue
                keys[user].append(key)

        return keys

    def do(self):
        for user, keys in self.get_keys().items():
            puts(user)
            puts('-' * 40)
            for key in keys:
                puts(key)
            puts('-' * 40)

list_keys = ListKeys()


class DisableKey(SshManagementTask):
    def disable_key(self, authorized_file, key):
        regex = re.escape(key)
        regex = regex.replace('\/', '/')
        backup = '.%s.bak' % self.current_time()
        files.comment(authorized_file, regex, use_sudo=True, backup=backup)

    @run_as_sudo
    def do(self):
        self.disable_key(self.conf.authorized_file, conf.key)


class DisableKeys(DisableKey):
    @run_as_sudo
    def do(self):
        authorized_files = list_authorized_files.get_authorized_files(
            exclude_users=self.conf.exclude_users)
        for user, authorized_file in authorized_files:
            self.disable_key(authorized_file, self.conf.key)


class EnableKey(SshManagementTask):
    def disable_key(self, authorized_file, key):
        regex = '%s' % re.escape(key)
        backup = '.%s.bak' % self.current_time()
        files.uncomment(authorized_file, regex, use_sudo=True, backup=backup)

    @run_as_sudo
    def do(self):
        self.enable_key(self.conf.authorized_file, self.conf.key)


class EnableKeys(EnableKey):
    @run_as_sudo
    def do(self):
        authorized_files = list_authorized_files.get_authorized_files(
            exclude_users=self.conf.exclude_users)
        for user, authorized_file in authorized_files:
            self.enable_key(authorized_file, conf.key)