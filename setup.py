from setuptools import setup

setup(
    name='awsautomate',
    version='0.2',
    author="Anil Menon",
    description="Utility to manage AWS instances",
    license="GPLv3+",
    packages=[''],
    url="https://github.com/anilmenon14/AWSAutomate",
    install_requires=[
        'click',
        'boto3'
    ],
    entry_points='''
        [console_scripts]
        awsautomate=awsautomate:cli
    ''',
)
