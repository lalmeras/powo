#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'ansible==2.3.2.0',
    'setuptools>=11.3',
    'Click==6.7',
    'm9dicts==0.4.0',
    'backports.tempfile==1.0rc1'
]

test_requirements = [
]

setup(
    name='powo',
    version='1.0.1rc',
    description="powo installer",
    long_description=readme + '\n\n' + history,
    author="Laurent Almeras",
    author_email='lalmeras@gmail.com',
    url='https://github.com/lalmeras/powo',
    packages=[
        'powo',
    ],
    package_dir={'powo':
                 'powo'},
    entry_points={
        'console_scripts': [
            'powo=powo.ansible:run'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="Apache Software License 2.0",
    zip_safe=False,
    keywords='powo',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
