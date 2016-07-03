#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'ansible==2.1.0.0',
    'Click>=6.0',
]

test_requirements = [
]

setup(
    name='powo',
    version='0.1.0',
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
            'powo=powo.cli:main'
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
