from setuptools import setup, find_packages

import cornflake

setup(
    name='cornflake',
    version=cornflake.__version__,
    long_description=cornflake.__doc__,
    author='Rupert Bedford',
    author_email='rupert.bedford@renalregistry.nhs.uk',
    url='https://github.com/renalreg/cornflake',
    packages=find_packages(),
    install_requires=[
        'bleach',
        'iso8601',
        'pytz',
        'six',
    ],
    extras_require={
        'sqlalchemy': ['SQLAlchemy']
    }
)
