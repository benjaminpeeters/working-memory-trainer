from setuptools import setup, find_packages

setup(
    name="working_memory_trainer",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        # No external dependencies required as curses is included in the Python standard library
    ],
    entry_points={
        "console_scripts": [
            "working-memory-trainer=memory_trainer:main",
        ],
    },
    author="Benjamin Peeters",
    author_email="benjamin.peeters@pik-potsdam.de",
    description="Terminal-based cognitive training application",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="memory, cognitive, training, terminal",
    url="https://github.com/username/working-memory-trainer",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Environment :: Console :: Curses",
        "Topic :: Games/Entertainment :: Puzzle Games",
    ],
    python_requires=">=3.6",
)