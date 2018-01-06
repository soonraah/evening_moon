from setuptools import setup, find_packages

with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='evening_moon',
    version='0.1.0',
    description='A Python library to get and analyze data of financial instruments '
                'for iDeCo provided by SBI Securities.',
    long_description=readme,
    author='soonraah',
    author_email='soonraah.dev@gmail.com',
    url='https://github.com/soonraah/evening_moon',
    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=['mock'],
    dependency_links=[],
    test_suite='tests'
)
