from fabric.api import env, sudo
from fabric.utils import puts, abort

from fabdeploy.containers import conf
from fabdeploy.task import Task
from fabdeploy import pip


__all__ = ['aptitude_install', 'setup_backports', 'install_common_software']


class AptitudeUpdate(Task):
    @conf
    def force(self):
        return False

    def do(self):
        if self.conf.force or not hasattr(env, '_aptitude_updated'):
            sudo('aptitude update')
            env._aptitude_updated = True

aptitude_update = AptitudeUpdate()


class AptitudeInstall(Task):
    @conf
    def options(self):
        return 'options'

    def do(self):
        aptitude_update.run()
        sudo('aptitude install %(options)s -y %(packages)s' % self.conf)

aptitude_install = AptitudeInstall()


BACKPORTS = {
    'lenny': ('http://backports.debian.org/debian-backports '
              'lenny-backports main contrib non-free'),
    'squeeze': ('http://backports.debian.org/debian-backports '
                'squeeze-backports main contrib non-free'),
    'natty': ('http://archive.ubuntu.com/ubuntu '
              'natty-backports main universe multiverse restricted'),
    'maverick': ('http://archive.ubuntu.com/ubuntu '
                 'maverick-backports main universe multiverse restricted'),
    'lucid': ('http://archive.ubuntu.com/ubuntu '
              'lucid-backports main universe multiverse restricted'),
}


class SetupBackports(Task):
    @conf
    def backports(self):
        if self.conf.os in BACKPORTS:
            return BACKPORTS[self.conf.os]

    def do(self):
        if not self.backports:
            puts('Backports are not available for %(os)s' % self.conf)
            return

        sudo("echo 'deb %(backports)s' > "
             "/etc/apt/sources.list.d/backports.sources.list" % self.conf)
        aptitude_update.run(force=True)

setup_backports = SetupBackports()


COMMON_PACKAGES = [
    'python', 'build-essential', 'python-dev', 'python-setuptools',
    'python-profiler', 'libjpeg-dev', 'zlib1g-dev',
    'libssl-dev', 'libcurl3-dev',
    'libxml2-dev', 'libxslt1-dev',  # for lxml

    'screen', 'locales-all', 'curl',
    'memcached',
    'subversion',
]

EXTRA_PACKAGES = {
    'lenny': ['libmysqlclient15-dev'],
    'squeeze': ['libmysqlclient-dev'],
    'natty': ['libmysqlclient-dev'],
    'maverick': ['libmysqlclient-dev'],
    'lucid': ['libmysqlclient-dev'],
}


class InstallCommonSoftware(Task):
    def do(self):
        if self.conf.os not in EXTRA_PACKAGES:
            abort('OS %(os)s is unsupported now.' % self.conf)
            return

        packages = ' '.join(COMMON_PACKAGES + EXTRA_PACKAGES[self.conf.os])
        aptitude_install.run(packages=packages)

        vcs_options = {
            'lenny': '-t lenny-backports',
        }
        aptitude_install.run(packages='mercurial git git-core',
                             options=vcs_options.get(self.conf.os, ''))
        aptitude_install.run(packages='bzr', options='--without-recommends')

        sudo('easy_install --upgrade pip')
        pip.install.run(app='virtualenv', upgrade=True)

install_common_software = InstallCommonSoftware()
