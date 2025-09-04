from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="nest-protect-mcp",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="MCP server for Nest Protect devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/nest-protect-mcp",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=[
        "fastmcp==2.12.0",
        "pydantic>=1.9.0",
        "aiohttp>=3.8.0",
        "python-dotenv>=0.20.0",
        "toml>=0.10.2",
        "python-dateutil>=2.8.2",
    ],
    entry_points={
        "console_scripts": [
            "nest-protect-mcp=nest_protect_mcp.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
