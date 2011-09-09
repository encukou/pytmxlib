#! /usr/bin/python
# Encoding: UTF-8

from setuptools import setup, find_packages, Command

__copyright__ = "Copyright 2011, Petr Viktorin"
__version__ = '0.1'
__email__ = 'encukou@gmail.com'

class PyTest(Command):
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        import pytest
        errno = pytest.main('--cov-report term-missing --cov tmxlib'.split())
        raise SystemExit(errno)

setup(
    name='tmxlib',
    version=__version__,
    install_requires=[
            'lxml>=2.3',
        ],
    setup_requires=[],
    tests_require=[
            'pytest',
            'pytest-cov',
            'formencode',
        ],
    packages=find_packages(),
    cmdclass={'test': PyTest},

    zip_safe = False,
)
