from fabric.api import run, task, env

@task
def check(txt):
    run("uname")
    run("echo {}".format(txt))

