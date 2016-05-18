import os


def getcwd():
    try:
        pwd = os.stat(os.environ['PWD'])
        cwd = os.stat(os.getcwd())
        if pwd.st_ino == cwd.st_ino and pwd.st_dev == cwd.st_dev:
            cwd = os.environ['PWD']
        else:
            cwd = os.getcwd()
    except:
        cwd = os.getcwd()
    return cwd
