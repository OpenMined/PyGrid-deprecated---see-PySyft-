import os
from setuptools import find_packages, setup


def get_requirements(req_file):
    """Read requirements file and return packages and git repos separately"""
    requirements = []
    dependency_links = []
    lines = read(req_file).split("\n")
    for line in lines:
        if line.startswith("git+"):
            dependency_links.append(line)
        else:
            requirements.append(line)
    return requirements, dependency_links


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


core_reqs, core_dependency_links = get_requirements("requirements.txt")


setup(
    name="openmined.gridnetwork",
    version="0.1.0",
    author="OpenMined",
    author_email="contact@openmined.org",
    description="A network router used by the PyGrid platform.",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/OpenMined/PyGridNetwork",
    maintainer="Benardi Nunes",
    maintainer_email="benardinunes@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=core_reqs,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={"console_scripts": ["raise_grid=gridnetwork:raise_grid"]},
    python_requires=">=3.5, <4",
    project_urls={
        "Bug Reports": "https://github.com/OpenMined/PyGridNetwork/issues",
        "Funding": "https://opencollective.com/openmined",
        "Source": "https://github.com/OpenMined/PyGridNetwork",
    },
)
