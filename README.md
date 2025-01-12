# Changelog Generator

A flexible, AI-powered changelog generator for Git repositories.

## Features

- 🚀 Automatic changelog generation from Git commit history
- 🤖 Optional AI-powered changelog enhancement
- 📝 Configurable changelog sections and output
- 🔧 Supports project-level configuration
- 💻 Easy-to-use CLI interface

## Prerequisites

- Python 3.8+
- Git
- Ollama (optional, for AI-powered changelog generation)

## Installation

```bash
pip install changelog_generator
```

## Usage

### Basic Usage

Generate a changelog in the current Git repository:

```bash
changelog_generator
```

### Configuration

Create a `.changelog.yaml` file in your project root to customize changelog generation:

```yaml
# Example .changelog.yaml configuration
git:
  repository_path: .
  branch: main
  # Optional: specify a specific commit range
  # commit_range: 'old_commit..new_commit'

changelog:
  sections:
    - type: feat
      title: "🚀 Features"
    - type: fix
      title: "🐛 Bug Fixes"

ai:
  enabled: true
  provider: ollama
  model_name: qwen2.5:14b
```

### CLI Options

```bash
# Generate changelog for a specific repository
python changelog_generator.py --repo /path/to/repo

# Generate changelog for a specific branch
python changelog_generator.py --branch develop

# Generate changelog for a specific commit range
python changelog_generator.py --commit-range "576ebd6..698b4d07"

# Changelogs are automatically saved with timestamped filenames
# e.g., CHANGELOG-YYYYMMDD_HHMMSS.md

# Use a custom configuration file
python changelog_generator.py --config /path/to/custom_config.yaml

# Enable verbose logging
python changelog_generator.py --verbose
```

## Configuration Options

### Git Settings
- `repository_path`: Path to the Git repository (default: current directory)
- `branch`: Branch to generate changelog for (default: main)
- `commit_range`: Specific commit range to generate changelog

### Changelog Settings
- `output_file`: Changelog output filename (default: CHANGELOG.md)
- `sections`: Customize changelog sections by commit type

### AI Settings
- `enabled`: Enable/disable AI-powered changelog generation
- `provider`: AI provider (ollama or xai)
- `model_name`: Specific AI model to use

### Logging Settings
- `level`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)

## AI Changelog Generation

The changelog generator supports AI-powered changelog generation using:
- Ollama (local AI models)
- XAI (Grok)

Ensure you have the necessary AI providers and models configured.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

Your Name - your.email@example.com

Project Link: [https://github.com/yourusername/changelog_generator](https://github.com/yourusername/changelog_generator)