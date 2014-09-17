from fabric.api import run, task

@task
def check():
    run("uname")

