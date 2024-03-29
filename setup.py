import sys

from setuptools import find_packages, setup

import bol


# Dynamically calculate the version based on bol.VERSION.
VERSION = bol.__version__

install_requires = ["python-dateutil", "requests"]

setup(
    name="python-bol-api",
    version=VERSION,
    description="Wrapper for the bol.com API",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
        "Topic :: System",
        "Topic :: System :: Software Distribution",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: "
        "GNU Lesser General Public License v3 or later (LGPLv3+)",
    ],
    keywords="bol bol.com api wrapper",
    author="Raymond Penners",
    author_email="raymond.penners@intenct.nl",
    url="http://www.intenct.info/",
    license="",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    entry_points="",
)
