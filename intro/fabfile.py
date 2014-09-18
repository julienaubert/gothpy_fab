from fabric.api import run, task, sudo, env

env.user = 'vagrant'
env.password = 'vagrant'
env.port = 2222
env.host_string = "localhost"


@task
def check(last, name):
    run("uname")
    run("echo {}".format(last, name))


