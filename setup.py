#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2020 Andrius Štikonas <andrius@stikonas.eu>
# SPDX-License-Identifier: MIT

import setuptools


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="neohubapi",
    version="0.6",
    description="Async library to communicate with Heatmiser NeoHub 2 API.",
    url="https://gitlab.com/neohubapi/neohubapi/",
    author="Andrius Štikonas",
    author_email="andrius@stikonas.eu",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'async_property',
    ],
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=setuptools.find_packages(),
    scripts=['scripts/neohub_cli.py'],
    keywords=['neohub', 'heatmiser'],
    zip_safe=True,
)
