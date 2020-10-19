from setuptools import setup, find_packages

setup(
    name="dota_match_dataset",
    version="0.1.0",
    description="A package to fetch public match dataset for DOTA",
    author="Zeynep Bicer",
    packages=find_packages(),
    entry_points={"console_scripts": [
        "dmd_fetch = dota_match_dataset.__main__:main",
    ]},
    install_requires=[
        "requests"
    ]
)
