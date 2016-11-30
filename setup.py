#!/usr/bin/env python


from setuptools import setup
from distutils.command.sdist import sdist
import os
import sys


class sdist_git(sdist):
    """Add revision number to version for development releases."""

    def run(self):
        if "dev" in self.distribution.metadata.version:
            self.distribution.metadata.version += self.get_tip_revision()
        sdist.run(self)

    def get_tip_revision(self, path=os.getcwd()):
        try:
            import git
        except ImportError:
            return ''
        try:
            repo = git.Repo('.')
        except git.InvalidGitRepositoryError:
            return ''
        return repo.head.commit.hexsha[:7]


install_requires = [
                    'requests',
                    'jsonmodels'
                    'pyjwt>1.3']
major_python_version, minor_python_version, _, _, _ = sys.version_info
if major_python_version < 3 or (major_python_version == 3 and minor_python_version < 4):
    install_requires.append('pathlib')

setup(
    name = "vsdConnect",
    version = "0.8.1dev",
    package_dir = {'vsdConnect': 'vsdConnect'},
    packages = ['vsdConnect'],
    long_description = open('README.md').read(),
    install_requires = install_requires,
    url = 'https://github.com/SICASFoundation/vsdConnect'

)
