from __future__ import print_function
from fabric.api import sudo, run, task, hide, with_settings, settings, prefix, cd, put, env
from fabric.contrib.files import exists
from fabric.colors import green, red
import logging
import re


env.user = 'vagrant'
env.password = 'vagrant'
env.port = 2222
env.host_string = 'localhost'


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='fab.log',
                    filemode='w')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger(__name__).addHandler(console)
log = logging.getLogger(__name__)


@with_settings(warn_only=True)
def test(cmd, expect_contains, error_msg=None):
    log.info('Checking `{}`..'.format(cmd))
    out = run(cmd)
    if expect_contains in out:
        log.info('{} {}'.format(expect_contains, green('OK')))
        return True
    else:
        log.error('{} {} {}'.format(red("FAIL!! "), out, error_msg or " expected: {}".format(expect_contains)))
        return False


@with_settings(warn_only=True)
def test_version(cmd, regex, min_required):
    if not run_ok(cmd):
        return False
    out = run(cmd)
    match = re.search(regex, out)
    actual_version = match.group('version') if match else None
    if not actual_version:
        log.error('{} - ran `{}`: could not extract version, out: "{}" regex: "{}"'
                  ''.format(red("FAIL!! "), cmd, out, regex))
        return False
    if tuple(actual_version.split('.')) < tuple(min_required.split('.')):
        log.info('{} - ran `{}`: actual {}, required {}'.format(red('FAIL'), cmd, actual_version, min_required))
        return False
    log.info('{} - ran `{}`: actual {}, required {}'.format(green('OK'), cmd, actual_version, min_required))
    return True


@with_settings(warn_only=True)
def run_ok(cmd):
    result = run(cmd)
    if not result.return_code == 0:
        log.info('{} - checked `{}`, out: {}'.format(red("FAIL"), cmd, result))
    else:
        log.info('{} - checked `{}`'.format(green("OK"), cmd))
    return result.return_code == 0


@task
def system_install():
    sudo("apt-get update")
    sudo("apt-get install git gettext")
    sudo("apt-get install uwsgi")
    sudo('wget https://bootstrap.pypa.io/ez_setup.py -O - | python')
    sudo('wget https://bootstrap.pypa.io/get-pip.py -O - | python')
    sudo('pip install -I virtualenvwrapper')
    sudo('pip install -I uwsgi')

    put('nginx.conf', '/etc/nginx/nginx.conf', use_sudo=True)
    with settings(hide('warnings'), warn_only=True):
        sudo('service nginx start')
    sudo('service nginx reload')


@task
def reload_nginx():
    put('nginx.conf', '/etc/nginx/nginx.conf', use_sudo=True)
    with settings(hide('warnings'), warn_only=True):
        sudo('service nginx start')
    sudo('service nginx reload')


@task
def system_check():
    ok = True
    version_regex = "(?P<version>(\d)+.(\d)+(.(\d))*)"
    with hide('everything'):
        ok &= test_version('python --version', version_regex, '2.7.3')
        ok &= test_version('git --version', version_regex, '1.7.9')
        ok &= run_ok('python -c "import setuptools"')
        ok &= test_version('pip --version', version_regex, '1.5')
        ok &= test_version('gettext --version', version_regex, '0.15')
        ok &= test_version('nginx -v', version_regex, '1.1')
        ok &= test_version('uwsgi --version', version_regex, '1.0')
    return ok


@task
def checkout(git_ref, git_url, target):
    def re_clone():
        run('rm -rf {}'.format(target))
        run('mkdir -p {}'.format(target))
        run('git clone {} {}'.format(git_url, target))

    if not exists(target):
        re_clone()
    with settings(hide('warnings'), warn_only=True):
        out = run('git config --get remote.origin.url')
    if out != git_url:
        re_clone()
    with cd(target):
        run('git fetch origin')
        # delete all local branches (avoid dealing with pulling)
        run('git checkout HEAD') # make sure not to be on a branch
        run('git branch -l | grep -v \* | xargs git branch -D')
        run('git checkout {}'.format(git_ref))


@task
def setup_user():
    put('.bash_profile', '~/.bash_profile')
    run('mkdir -p ~/projects')


@task
def deploy(git_ref="master", git_url="https://github.com/julienaubert/gothpy_django.git", django_version="1.6"):
    if not system_check():
        return
    setup_user()
    checkout(git_ref, git_url, 'build')
    with cd('build'):
        run('python setup.py sdist')
        pkg_path = run('ls dist/*.tar.gz -1 | xargs readlink -f')
    with settings(warn_only=True):
        out = run('mkproject gothpy_django')
        if out.return_code != 0 and 'already exists' not in out:
            log.error(out)
            return
    with prefix('workon gothpy_django'):
        run('pip install {}'.format(pkg_path))
        requirements_pip = '$VIRTUAL_ENV/lib/python2.7/site-packages/gothpy_django_ex/requirements/testing.pip'
        run('pip install --force-reinstall -r {}'.format(requirements_pip))
        run('pip install --force-reinstall django=={}'.format(django_version))

        django_settings = '$VIRTUAL_ENV/lib/python2.7/site-packages/gothpy_django_ex/settings/local.py'
        run('cp {} .'.format(django_settings))
        run('django-admin.py collectstatic --noinput')
        run('django-admin.py syncdb --noinput')


        run('django-admin.py runserver 8000')

        # wsgi_file = '$VIRTUAL_ENV/lib/python2.7/site-packages/gothpy_django_ex/wsgi.py'
        # run('cp {} .'.format(wsgi_file))

@task
def startapp():
    with prefix('workon gothpy_django'):
        run('django-admin.py runserver 8000')


    # put('uwsgi.ini', '~/uwsgi.ini')
    # with prefix('workon gothpy_django'):
    #     run('uwsgi --ini ~/uwsgi.ini')
