from __future__ import print_function
from fabric.api import sudo, run, task, hide, settings, with_settings, cd, put
from fabric.contrib.files import exists
from fabric.colors import green, red
import logging
import re


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
    sudo("apt-get install git")
    sudo('wget https://bootstrap.pypa.io/ez_setup.py -O - | python')
    sudo('wget https://bootstrap.pypa.io/get-pip.py -O - | python')
    sudo('pip install -I virtualenvwrapper')


@task
def system_check():
    ok = True
    version_regex = "(?P<version>(\d)+.(\d)+(.(\d))*)"
    with hide('everything'):
        ok &= test_version('python --version', version_regex, '2.7.3')
        ok &= test_version('git --version', version_regex, '1.7.9')
        ok &= run_ok('python -c "import setuptools"')
        ok &= test_version('pip --version', version_regex, '1.5')
    return ok

@task
def checkout(git_ref, git_url, target):
    def re_clone():
        run('rm -rf {}'.format(target))
        run('mkdir -p {}'.format(target))
        run('git clone {} {}'.format(git_url, target))

    if not exists(target):
        re_clone()
    with cd(target):
        run('git fetch origin')
        run('git checkout origin/master')

@task
def setup_user():
    put('.bashrc', '~/.bashrc')
    put('.extra', '~/.extra')
    run('source ~/.bashrc')
    run('mkdir -p ~/projects')

@task
def deploy(git_ref="master", git_url="https://github.com/shacker/django-todo"):
    if not system_check():
        return
    setup_user()
    checkout(git_ref, git_url, 'build')
    with cd('build'):
        run('python setup.py sdist')
        pkg_path = run('ls dist/*.tar.gz -1 | xargs readlink -f')
    run('mkproject django_todo')
    run('workon django_todo')
    run('pip install ./dist/*.tar.gz')

