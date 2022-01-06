import os

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# todo: pull git commit
# rk: not sure how useful the git commit would be in the version

# import subprocess
#
#
# def get_commit_hash():
#     cmd = ['git', 'show', '--pretty="%h"']
#     try:
#         return subprocess.check_output(cmd).decode('utf8').strip()
#     except Exception as e:
#         return ''


version = os.environ.get("PYPI_VERSION", "0.0.0.dev0+local")

setup(
    name="umls-rat",
    version=version,
    description="UMLS RAT (REST API Tool) provides a reasonable "
    "interface to the UMLS MetaThesaurus via the REST API.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Russell Klopfer",
    author_email="rklopfer@mmm.com",
    url="https://github.mmm.com/OneNLU/umls-rat",
    include_package_data=True,
    packages=find_packages(),
    install_requires=["requests", "requests-cache"],
    python_requires=">=3.7",
)
