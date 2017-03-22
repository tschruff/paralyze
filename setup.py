from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))


def readme():
    with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
        return f.read()


setup(
    name='paralyze',
    version='0.1.0a1',
    description='A scientific parallel framework for geometry analysis',
    long_description=readme(),

    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5'
    ],

    keywords='scientific parallel geometry analysis',
    url='https://github.com/scruffy-t/paralyze',
    author='Tobias Schruff',
    author_email='tobias.schruff@gmail.com',
    license='BSD',
    packages=['paralyze'],

    install_requires=['numpy', 'jinja2', 'paramiko'],

    # additional data will be installed relative to sys.prefix
    # list of (install_folder, [list_of_files_to_be_installed])
    data_files=[('data', ['data/workspace.json'])],

    # we use "nose" for tests
    # $ python setup.py test
    # to execute the test suite
    test_suite='nose.collector',
    tests_require=['nose'],

    entry_points={
        'console_scripts': [
            'paralyze.csb=paralyze.apps.csb_cli:main',
            'paralyze.job=paralyze.apps.job_cli:main',
            'paralyze.workspace=paralyze.apps.workspace_cli:main'
        ],
    },

    include_package_data=True,
    zip_safe=False
)
