#!/usr/bin/env python3
"""Setup script for pihole6api."""

from setuptools import setup, find_packages

setup(
    name="pihole6api",
    version="0.2.0",
    description="Python API Client for Pi-hole 6",
    author="Shane Barbetta",
    author_email="shane@barbetta.me",
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.26.0",
    ],
    extras_require={
        "test": [
            "pytest>=6.0",
            "pytest-cov>=3.0.0",
            "pytest-mock>=3.6.0",
            "coverage>=6.0",
        ],
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=3.0.0",
            "pytest-mock>=3.6.0",
            "coverage>=6.0",
            "black>=22.0",
            "isort>=5.0",
            "flake8>=4.0",
            "mypy>=0.900",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords=["pihole", "dns", "adblocking", "api", "client"],
    url="https://github.com/sbarbett/pihole6api",
    project_urls={
        "Documentation": "https://github.com/sbarbett/pihole6api",
        "Source": "https://github.com/sbarbett/pihole6api",
        "Issues": "https://github.com/sbarbett/pihole6api/issues",
    },
)