from setuptools import setup, find_packages

import cornflake

setup(
    name='cornflake',
    version=cornflake.__version__,
    long_description=cornflake.__doc__,
    author='Rupert Bedford',
    author_email='rupert.bedford@renalregistry.nhs.uk',
    url='https://www.renalreg.org/',
    packages=find_packages(),
    install_requires=[
        'bleach',
        'python-dateutil',
        'pytz',
        'six',
    ],
    extras_require={
        'sqlalchemy': ['SQLAlchemy']
    }
)
