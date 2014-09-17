from __future__ import print_function
from fabric.api import run, task, env

env.host_string = 'localhost'
env.port = 2222
env.user = 'vagrant'
env.password = 'vagrant'

@task
def check(txt):
    #import pprint
    #pp = pprint.PrettyPrinter()
    #pp.pprint(env)
    run("uname")
    run("echo {}".format(txt))

