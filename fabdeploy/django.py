from fabric.api import run
from fabric.contrib import files

from fabdeploy.containers import conf
from fabdeploy.task import Task
from fabdeploy.utils import inside_django


__all__ = ['push_settings', 'manage', 'syncdb', 'migrate', 'collectstatic']


class PushSettings(Task):
    @conf
    def from_file(self):
        return self.conf.django_lpath_getter(self.conf.remote_settings_file)

    @conf
    def to_file(self):
        return self.conf.django_path_getter(self.conf.local_settings_file)

    def do(self):
        files.upload_template(self.conf.from_file, self.conf.to_file,
                              context=self.conf, use_jinja=True)

push_settings = PushSettings()


class Manage(Task):
    @inside_django
    def do(self):
        run('python manage.py %(command)s' % self.conf)

manage = Manage()


class Syncdb(Manage):
    @conf
    def command(self):
        return 'syncdb --noinput'

syncdb = Syncdb()


class Migrate(Manage):
    @conf
    def command(self):
        return 'migrate --noinput'

migrate = Migrate()


class Collectstatic(Manage):
    @conf
    def command(self):
        return 'collectstatic --noinput'

collectstatic = Collectstatic()