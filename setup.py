#!/usr/bin/env python3

from codecs import open
from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='blue-audio-con',
    version='0.1.0',
    description='assistant for connecting to bluetooth audio devices',
    long_description=long_description,
    url='https://github.com/N-Coder/blue-audio-con',
    author='Niko Fink',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
    ],
    entry_points={
        "console_scripts": [
            "blue-audio-con = blue_audio_con.main:main",
        ]
    },
    packages=find_packages(),
    package_data={
        'blue_audio_con': ['include/*'],
    },
    install_requires=[
        'pexpect',
        'PyGObject',
        'pulsectl'
    ]
)
