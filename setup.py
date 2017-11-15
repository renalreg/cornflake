import re
from setuptools import setup, find_packages

# https://github.com/kennethreitz/requests/blob/v2.11.1/setup.py#L50
with open('cornflake/__init__.py', 'r') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

setup(
    name='cornflake',
    version=version,
    description='A simple library for converting to and from Python objects',
    author='Rupert Bedford',
    author_email='rupert.bedford@renalregistry.nhs.uk',
    url='https://github.com/renalreg/cornflake',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'bleach',
        'iso8601',
        'pytz',
        'six',
    ],
    extras_require={
        'sqlalchemy': ['SQLAlchemy']
    },
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ]
)
