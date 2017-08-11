from setuptools import setup

setup(
    name='preservicaservice',
    version='0.1.0',
    description='Provides service service.',
    install_requires=[
        'amazon_kclpy',
        'boto3',
        'dicttoxml',
        'lxml',
    ],
    tests_require=[
        'autopep8',
        'pep8',
        'pytest',
        'pre-commit',
        'moto',
    ],
    license='Apache',
    author='Andrew Griffiths',
    packages=['preservicaservice'],
    entry_points={
        'console_scripts': [
            'preservicaservice = preservicaservice.preservicaservice:main',
        ],
    },
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
)
