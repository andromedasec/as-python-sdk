from setuptools import setup

setup(
    name='as-python-sdk',
    version='1.0.0',
    description='Andromeda Security Python SDK',
    url='https://github.com/andromedasec/as-python-sdk',
    author='Andromeda Security',
    author_email='support@andromedasecurity.com',
    license='Andromeda Security',
    packages=['as-python-sdk'],
    install_requires=[
        "PyYAML==6.0.2",
        "gql[all]==3.5.0",
        "polling2==0.5.0",
        "protobuf==5.29.6",
        "requests==2.32.3",
        "requests_mock==1.12.1",
        "google-api-core==2.21.0",
    ],
    classifiers=[
        'Development Status :: 1 - Development',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.12',
    ],
)
