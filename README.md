# Changelog Generator

A flexible, AI-powered changelog generator for Git repositories.

## Features

- 🚀 Automatic changelog generation from Git commit history
- 🤖 Optional AI-powered changelog enhancement
- 📝 Configurable changelog sections and output
- 🔧 Supports project-level configuration
- 💻 Easy-to-use CLI interface
- 🔍 Supports custom commit ranges and branch selection
- 📁 Automatically saves changelog with timestamped filenames
- 🔄 Modular AI provider architecture for easy extension
- 🎛 Version information available via `--version` flag

## Prerequisites

- Python 3.8+
- Git
- Ollama (optional, for AI-powered changelog generation)
- **requirements.txt**: A file specifying the project's dependencies.
  - This file lists all Python packages and their versions required for the project to function correctly.

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

Create a `.changelog.yaml` file in your project root to customize changelog generation. Here's an example configuration:

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
  output_file: "CHANGELOG.md"

ai:
  enabled: true
  provider: ollama
  model_name: qwen3:latest
```

### CLI Options

The changelog generator provides several CLI options for customization:

```bash
# Generate changelog for a specific repository
python -m changelog_generator.main --repo /path/to/repo

# Generate changelog for a specific branch
python -m changelog_generator.main --branch develop

# Generate changelog for a specific commit range
python -m changelog_generator.main --commit-range "576ebd6..698b4d07"

# Use a custom configuration file
python -m changelog_generator.main --config /path/to/custom_config.yaml

# Enable verbose logging
python -m changelog_generator.main --verbose

# Display version information
python -m changelog_generator.main --version
```

Changelogs are automatically saved with timestamped filenames (e.g., CHANGELOG-YYYYMMDD_HHMMSS.md).

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
- `provider`: AI provider (ollama, xai, or anthropic)
- `model_name`: Specific AI model to use

### Logging Settings

- `level`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)

## AI Changelog Generation

The changelog generator supports AI-powered changelog generation using:

- Ollama (local AI models)
- XAI (Grok)
- Anthropic (via API)

To use AI-powered changelog generation:

1. Ensure you have the necessary AI providers and models configured.
2. Set `ai.enabled` to `true` in your `.changelog.yaml` file.
3. Specify your preferred AI `provider` and `model_name`.

## Troubleshooting

### Common Issues

1. **Git repository not found**:
   - Ensure you're running the command in a Git repository directory.
   - Check if the `repository_path` in `.changelog.yaml` is correct.

2. **AI provider not configured**:
   - Verify that your AI provider (Ollama, XAI, or Anthropic) is properly installed and configured.
   - Check the `ai` section in your `.changelog.yaml` for correct settings.

3. **Configuration file not found**:
   - Ensure `.changelog.yaml` is in your project root.
   - Use the `--config` CLI option to specify a custom configuration file path.

### Debugging Tips

- Use the `--verbose` CLI option to enable detailed logging.
- Check the generated log files for error messages.

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

## Additional Resources

- [Example `.changelog.yaml` configuration](.changelog.yaml.example)
- [Project Changelog Example](CHANGELOG.md)
