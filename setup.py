from setuptools import setup, find_packages

setup(
    name='changelog_generator',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'gitpython',
        'python-dotenv',
        'langchain',
        'langchain-community',
        'langchain-openai',
        'openai',
        'spacy',
        'pyyaml',
        'semantic-version',
    ],
    entry_points={
        'console_scripts': [
            'changelog-generator=changelog_generator:main',
        ],
    },
)
