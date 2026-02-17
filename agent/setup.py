import os
from pathlib import Path
from setuptools import setup, find_packages
from setuptools.command.build_ext import build_ext

from apminsight import version

HERE = Path(__file__).resolve().parent

def load_module_from_project_file(mod_name, fname):
    fpath = HERE / fname
    import importlib.util
    spec = importlib.util.spec_from_file_location(mod_name, fpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def get_exts_for(name):
    try:
        mod = load_module_from_project_file(
            "apminsight.dependency.{}.setup".format(name), "apminsight/dependency/{}/setup.py".format(name)
        )
        return mod.get_extensions()
    except Exception as e:
        print("WARNING: module loading for %s extensions, skipping: %s" % (name, e))
        return []

with open("README.md", "r") as fh:
    long_description = fh.read()

setup_kwargs = {
    "name": "apminsight",
    "version": version,
    "description": "Site24x7 application performance monitoring",
    "url": "https://site24x7.com",
    "author": "Zoho Corporation Pvt. Ltd.",
    "author_email": "apm-insight@zohocorp.com",
    "maintainer": "ManageEngine Site24x7",
    "maintainer_email": "apm-insight@zohocorp.com",
    "long_description": long_description,
    "long_description_content_type": "text/markdown",
    "license": "LICENSE.txt",
    "include_package_data": True,
    "python_requires": ">=3.7",
    "entry_points": {
        "console_scripts": [
            "apminsight-run = apminsight.commands.apm_run:main",
        ],
    },
    "zip_safe": False,
}

if "APM_INCLUDE_DEPENDENCY" in os.environ:
    setup_kwargs.update({
        "cmdclass": {"build_ext": build_ext},
        "ext_modules": get_exts_for('psutil'),
        "packages": find_packages(exclude=["tests", "tests.*"]),
    })
else:
    setup_kwargs.update({
        "install_requires": ["psutil"],
        "packages": find_packages(exclude=["tests", "tests.*", "apminsight.dependency", "apminsight.dependency.*"]),
    })

setup(**setup_kwargs)
