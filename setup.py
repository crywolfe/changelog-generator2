from setuptools import setup, find_packages

setup(
    name="changelog_generator",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "gitpython",
        "python-dotenv",
        "langchain-community",
        "pyyaml",
        "black",
        "requests",
        "ollama",
        "tenacity"
    ],
    entry_points={
        "console_scripts": [
            "changelog-generator=changelog_generator.main:main"
        ]
    },
)
