# Git Changelog Generator

## Overview

This Python script generates a detailed changelog between two Git commits, helping you track changes in your repository.

## Prerequisites

- Python 3.7+
- GitPython library

## Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd <repository-directory>
```

2. Create a virtual environment (optional but recommended):
```bash
python3 -m venv changelog_env
source changelog_env/bin/activate  # On Windows, use `changelog_env\Scripts\activate`
```

3. Install dependencies:
```bash
pip install GitPython
```

## Usage

### Basic Usage

Generate a changelog between two commits:
```bash
python changelog_generator.py <commit1> <commit2>
```

### Examples

1. Compare the last 5 commits with the current HEAD:
```bash
python changelog_generator.py HEAD~5 HEAD
```

2. Compare specific commit hashes:
```bash
python changelog_generator.py abc1234 def5678
```

3. Specify a different repository path:
```bash
python changelog_generator.py HEAD~3 HEAD --repo /path/to/your/repo
```

## Arguments

- `commit1`: First commit hash or reference
- `commit2`: Second commit hash or reference
- `--repo`: Optional path to the Git repository (default is current directory)

## Troubleshooting

- Ensure you're in a valid Git repository
- Verify commit references exist
- Check that GitPython is correctly installed

## Future Improvements

- Markdown changelog generation
- More detailed diff information
- LLM-powered changelog analysis

## License

[Specify your license here]
