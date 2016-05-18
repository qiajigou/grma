from grma import __version__

from setuptools import setup, find_packages

setup(
    name='grma',
    version=__version__,

    description='Simple gRPC Python manager',
    author='GuoJing',
    author_email='soundbbg@gmail.com',
    license='MIT',
    url='https://github.com/qiajigou/grma',
    zip_safe=False,
    packages=find_packages(exclude=['examples', 'tests']),
    include_package_data=True,
    entry_points="""
    [console_scripts]
    grma=grma.app:run
    """,
    install_requires=[
        'setproctitle==1.1.10'
    ]
)
