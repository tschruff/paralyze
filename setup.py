from codecs import open
from os import path

from setuptools import setup
from setuptools.command.install import install

from paralyze import __version__

import paralyze.core.solids as solids

here = path.abspath(path.dirname(__file__))


class InstallCommand(install):
    description = ''
    user_options = install.user_options + [
        ('solid_dtype=', 'float32', "default numpy dtype of solids' data")
    ]

    def initialize_options(self):
        install.initialize_options(self)
        self.solid_dtype = 'float32'

    def finalize_options(self):
        install.finalize_options(self)

    def run(self):
        solids.DEFAULT_DTYPE = self.solid_dtype
        install.run(self)


def readme():
    with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
        return f.read()


setup(
    name='paralyze',
    version=__version__,
    description='A scientific framework for parallel computational geometry',
    long_description=readme(),

    cmdclass={
        'install': InstallCommand
    },

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

    install_requires=['numpy', 'jinja2', 'scipy', 'pyevtk', 'matplotlib'],

    # additional data will be installed relative to sys.prefix
    # list of (install_folder, [list_of_files_to_be_installed])
    data_files=[('data', ['data/settings.json'])],

    # we use "nose" for tests
    # $ python setup.py test
    # to execute the test suite
    test_suite='nose.collector',
    tests_require=['nose'],

    entry_points={
        'console_scripts': [
            'paralyze.csb=apps.csb_cli:main',
            'paralyze.job=apps.job_cli:main',
            'paralyze.workspace=apps.workspace_cli:main'
        ],
    },

    include_package_data=True,
    zip_safe=False
)
