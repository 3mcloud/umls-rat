from setuptools import setup, find_packages

with open("README.rst", "r", encoding="utf-8") as fh:
    long_description = fh.read()

version = "0.6.3"

setup(
    name="umls-rat",
    version=version,
    description="UMLS RAT (REST API Tool) provides a reasonable "
    "interface to the UMLS MetaThesaurus via the REST API.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    author="Russell Klopfer",
    author_email="rklopfer@mmm.com",
    url="https://github.com/3mcloud/umls-rat",
    include_package_data=True,
    packages=find_packages(),
    install_requires=["requests", "requests-cache>=1.0.0a0", "ratelimit", "backoff"],
    python_requires=">=3.7",
)
