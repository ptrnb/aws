#!usr/bin/env python3

from setuptools import setup

setup(
    name='aws_vpc_tools',
    version='0.1.0',
    description='Custom boto3 tools for interacting with AWS',
    url='https://github.com/ptrnb/aws',
    author='Peter Brown',
    license='MIT',
    packages=['aws','aws.tools'],
    install_requires=['ipaddress', 'boto3', 'botocore'],
    include_package_data=True,
    zip_safe=False)
