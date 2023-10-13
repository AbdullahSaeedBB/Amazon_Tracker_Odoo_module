import os
import subprocess
import sys


class Packages:
    """
    It's for tracker.py to install all required libraries.
    """

    get_pckg = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'])
    installed_packages = [r.decode().split('==')[0] for r in get_pckg.split()]

    # List of your required packages
    required_packages = ['cachecontrol', 'filelock', 'bs4', 'base64', 'random', 'simplejson']
    for packg in required_packages:
        if packg in installed_packages:
            pass
        else:
            os.system('pip3 install ' + packg)