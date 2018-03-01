# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import codecs
import os
import subprocess
from setuptools import setup, find_packages
from gitlab_registry_usage._version import __version__


def get_long_description_from_readme(readme_filename='README.md'):
    rst_filename = '{}.rst'.format(os.path.splitext(os.path.basename(readme_filename))[0])
    created_tmp_rst = False
    if not os.path.isfile(rst_filename):
        try:
            subprocess.check_call(['pandoc', readme_filename, '-t', 'rst', '-o', rst_filename])
            created_tmp_rst = True
        except (OSError, subprocess.CalledProcessError):
            import logging
            logging.warning('Could not convert the readme file to rst.')
    long_description = None
    if os.path.isfile(rst_filename):
        with codecs.open(rst_filename, 'r', 'utf-8') as readme_file:
            long_description = readme_file.read()
    if created_tmp_rst:
        os.remove(rst_filename)
    return long_description


long_description = get_long_description_from_readme()

setup(
    name='gitlab-registry-usage',
    version=__version__,
    packages=find_packages(),
    install_requires=[
        'pyOpenSSL',
        'requests'
    ],
    entry_points={
        'console_scripts': [
            'gitlab-registry-usage = gitlab_registry_usage.cli:main',
        ]
    },
    author='Ingo Heimbach',
    author_email='i.heimbach@fz-juelich.de',
    description='This is a package for querying the size of images in a GitLab registry.',
    long_description=long_description,
    license='MIT',
    url='https://github.com/IngoHeimbach/gitlab-registry-usage',
    keywords=['Git', 'GitLab', 'Docker', 'Registry', 'disk capacity'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Version Control :: Git',
        'Topic :: System :: Systems Administration',
    ]
)
