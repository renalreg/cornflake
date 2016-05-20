from setuptools import setup, find_packages

setup(
    name='cornflake',
    version='0.2.0',
    description='A simple library for converting to and from Python objects',
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
