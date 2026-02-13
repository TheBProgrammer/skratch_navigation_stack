from setuptools import find_packages, setup
import os
from glob import glob

package_name = "skratch_bringup"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name), glob("launch/*.py")),
        (os.path.join("share", package_name), glob("config/*")),
    ],
    install_requires=[],          # don't list setuptools here
    zip_safe=True,
    maintainer="kelo",
    maintainer_email="kelo@todo.todo",
    description="TODO: Package description",
    license="TODO: License declaration",
    # tests_require removed (deprecated)
    entry_points={
        "console_scripts": [
            # e.g. "foo = skratch_bringup.foo:main",
            'wheels_to_joint_states = skratch_bringup.wheels_to_joint_states:main',
        ],
    },
)
