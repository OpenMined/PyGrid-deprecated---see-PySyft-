from setuptools import setup

setup(
    name="OpenMined PyGrid CLI",
    version="0.0.1",
    packages=["apps.cli",],
    install_requires=["click", "PyInquirer"],
    entry_points="""
        [console_scripts]
        pygrid=apps.cli.cli:cli
    """,
)
