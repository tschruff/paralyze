from setuptools import setup


def readme():
    with open('README.rst', 'r') as f:
        return f.read()


setup(
    name='paralyze',
    version='0.1.0a1',
    description='A framework to analyze fields and bodies',
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

    keywords='scientific parallel data analysis',
    url='https://github.com/scruffy-t/paralyze',
    author='Tobias Schruff',
    author_email='tobias.schruff@gmail.com',
    license='BSD',
    packages=['paralyze'],

    # we use "nose" for tests
    # $ python setup.py test
    # to execute the test suite
    test_suite='nose.collector',
    tests_require=['nose'],

    entry_points={
        'console_scripts': [
            'paralyze_csb=paralyze.apps.csb_cli:main',
            'paralyze_job=paralyze.apps.job_cli:main',
            'paralyze_workspace=paralyze.apps.workspace_cli:main'
        ],
    },

    include_package_data=True,
    zip_safe=False
)
