from fabric.api import sudo, settings

from fabdeploy.containers import conf
from fabdeploy.task import Task as BaseTask
from fabdeploy.utils import upload_config_template


__all__ = ['install', 'd', 'ctl', 'shutdown', 'update', 'push_configs',
           'stop_programs', 'restart_programs']


class Task(BaseTask):
    pass


class Install(Task):
    def do(self):
        sudo('pip install --upgrade supervisor')

install = Install()


class D(Task):
    def do(self):
        with settings(warn_only=True):
            sudo('supervisord --configuration=%(supervisord_config)s' % self.conf)

d = D()


class Ctl(Task):
    """Perform ``command`` or show supervisor console."""

    @conf
    def command(self):
        return self.conf.get('command', '')

    def do(self):
        sudo('supervisorctl --configuration=%(supervisord_config)s '
             '%(command)s' % self.conf)

ctl = Ctl()


class Shutdown(Ctl):
    """Shutdown supervisord."""

    @conf
    def command(self):
        return 'shutdown'

shutdown = Shutdown()


class Update(Ctl):
    @conf
    def command(self):
        return 'update'

update = Update()


class PushConfigs(Task):
    """Push configs for ``supervisor_programs``."""

    def do(self):
        if 'supervisord_config_template' in self.conf:
            upload_config_template(self.conf.supervisord_config_template,
                                   self.conf.supervisord_config,
                                   context=self.conf)

        for _, _, programs in self.conf.supervisor_programs:
            for program in programs:
                config = '%s.conf' % program
                from_filepath = 'supervisor/%s' % config
                to_filepath = '%s/%s' % (self.conf.supervisor_config_path,
                                         config)
                upload_config_template(from_filepath,
                                       to_filepath,
                                       context=self.conf)

push_configs = PushConfigs()


class ProgramsCommand(Task):
    def get_group_command(self, group):
        self.conf.group = group
        return '%(command)s %(supervisor_prefix)s%(group)s:' % self.conf

    def get_program_command(self, program):
        self.conf.program = program
        return '%(command)s %(supervisor_prefix)s%(program)s' % self.conf

    def do(self):
        for _, group, programs in self.conf.supervisor_programs:
            for program in programs:
                ctl.run(command=self.get_program_command(program))


class RestartPrograms(ProgramsCommand):
    """Restart ``supervisor_programs``."""

    @conf
    def command(self):
        return 'restart'

restart_programs = RestartPrograms()


class StopPrograms(ProgramsCommand):
    """Stop ``supervisor_programs``."""

    @conf
    def command(self):
        return 'stop'

stop_programs = StopPrograms()
