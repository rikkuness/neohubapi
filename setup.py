#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2020 Andrius Štikonas <andrius@stikonas.eu>
# SPDX-License-Identifier: MIT

import setuptools

setuptools.setup(
    name = "neohubapi",
    version = "0.1",
    description = "Async library to communicate with Heatmiser NeoHub 2 API.",
    url = "https://gitlab.com/neohubapi/neohubapi/",
    author = "Andrius Štikonas",
    author_email = "andrius@stikonas.eu",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    install_requires = ['neohubapi'],
    keywords = ['neohub', 'heatmiser'],
    zip_safe = True,
)
