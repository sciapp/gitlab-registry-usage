import os
import runpy
from setuptools import setup, find_packages


def get_version_from_pyfile(version_file="gitlab_registry_usage/_version.py"):
    file_globals = runpy.run_path(version_file)
    return file_globals["__version__"]


def get_long_description_from_readme(readme_filename="README.md"):
    long_description = None
    if os.path.isfile(readme_filename):
        with open(readme_filename, "r", encoding="utf-8") as readme_file:
            long_description = readme_file.read()
    return long_description


version = get_version_from_pyfile()
long_description = get_long_description_from_readme()

setup(
    name="gitlab-registry-usage",
    version=version,
    packages=find_packages(),
    python_requires="~=3.3",
    install_requires=["pyOpenSSL", "requests", "typing", "yacl"],
    entry_points={"console_scripts": ["gitlab-registry-usage = gitlab_registry_usage.cli:main"]},
    author="Ingo Meyer",
    author_email="i.meyer@fz-juelich.de",
    description="This is a package for querying the size of repositories in a GitLab registry.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://github.com/sciapp/gitlab-registry-usage",
    keywords=["Git", "GitLab", "Docker", "Registry", "disk capacity"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Version Control :: Git",
        "Topic :: System :: Systems Administration",
    ],
)
