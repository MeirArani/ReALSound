from setuptools import setup

setup(
    name="realsound",
    version="1.0",
    install_requires=[
        "requests",
        'importlib-metadata; python_version<"3.10"',
    ],
)
