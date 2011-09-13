#! /usr/bin/python
# Encoding: UTF-8

from setuptools import setup, find_packages, Command

__version__ = '0.1.0'

class PyTest(Command):
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        import pytest
        errno = pytest.main([])
        raise SystemExit(errno)

setup(
    name='tmxlib',
    version=__version__,
    description='TMX tile map utilities',
    author='Petr Viktorin',
    author_email='encukou@gmail.com',
    classifiers=[x.strip() for x in """
            Development Status :: 4 - Beta
            Intended Audience :: Developers
            License :: OSI Approved :: MIT License
            Operating System :: OS Independent
            Programming Language :: Python :: 2.7
            Topic :: Games/Entertainment
        """.splitlines() if x.strip()],
    install_requires=[
            'lxml>=2.3',
            'pypng>=0.0.12',
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

try:
    import tmxlib
except ImportError:
    pass
else:
    if __version__ != tmxlib.__version__:
        print 'WARNING! setup.py / __init__.py version mismatch!'
