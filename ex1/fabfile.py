from __future__ import print_function
from fabric.api import run, task, hide, settings
from fabric.colors import green, red
import logging


logging.basicConfig(
    level=logging.DEBUG,
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


def test(cmd, expect_contains, error_msg=None):
    log.info('Checking `{}`..'.format(cmd))
    with settings(warn_only=True):
        out = run(cmd)
        if expect_contains in out:
            log.info('{} {}'.format(expect_contains, green('OK')))
            return True
        else: 
            log.error('{} {} {}'.format(
                red("FAIL!! "), 
                out, 
                error_msg or " expected: {}".format(expect_contains)))
            return False


@task
def check():
    with hide('everything'):
        test('python --version', '2.7.3')
        test('uname', 'Linux')

