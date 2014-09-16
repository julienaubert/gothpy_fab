from fabric.api import run, task, env

env.port = 2222

@task
def check(txt):
    import pprint
    pp = pprint.PrettyPrinter()
    pp.pprint(env)
    run("uname")
    run("echo {}".format(txt))

