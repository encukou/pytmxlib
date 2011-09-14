#! /usr/bin/python
# Encoding: UTF-8

import sys
from setuptools import setup, find_packages

__version__ = '0.1.0'


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
            Programming Language :: Python :: 2
            Programming Language :: Python :: 2.6
            Programming Language :: Python :: 2.7
            Programming Language :: Python :: 3
            Programming Language :: Python :: 3.1
            Programming Language :: Python :: 3.2
            Topic :: Games/Entertainment
        """.splitlines() if x.strip()],
    use_2to3=True,
    install_requires=[
            'lxml>=2.3',
        ],
    setup_requires=[],
    tests_require=[
            'pytest',
            'pytest-cov',
            'pytest-pep8',
        ],
    packages=find_packages(exclude=['.tox', '*.egg', 'build']),
    test_suite='tmxlib.test.run',

    package_data={'tmxlib': ['test/data/*']},
    zip_safe=False,
)

try:
    import tmxlib
except ImportError:
    pass
else:
    if __version__ != tmxlib.__version__:
        print('WARNING! setup.py / __init__.py version mismatch!')
