#! /usr/bin/python
# Encoding: UTF-8

from setuptools import setup, find_packages

__version__ = '0.2.0'


test_requirements = [
    'pytest',
    'pytest-cov',
    'pytest-pep8',
    'numpy',
    'pillow',
]

test_requirements = [
    'six',
    'pypng>=0.0.14',
]

setup(
    name='tmxlib',
    version=__version__,
    description='Library for manipulating TMX tile maps',
    url='http://pytmxlib.readthedocs.org',
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
            Programming Language :: Python :: 3.2
            Programming Language :: Python :: 3.3
            Topic :: Games/Entertainment
        """.splitlines() if x.strip()],
    install_requires=[
            'six',
            'pypng>=0.0.14',
        ],
    setup_requires=[],
    tests_require=test_requirements,
    packages=find_packages(exclude=['.tox', '*.egg', 'build']),

    zip_safe=False,

    extras_require={
        'test': test_requirements,
        'canvas': ['numpy'],
    },
)

try:
    import tmxlib
except ImportError:
    pass
else:
    if __version__ != tmxlib.__version__:
        print('WARNING! setup.py / __init__.py version mismatch!')
