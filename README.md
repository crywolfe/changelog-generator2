# Changelog Generator

A flexible, AI-powered changelog generator for Git repositories that creates beautiful, structured changelogs from your commit history.

## ✨ Features

- 🚀 **Automatic changelog generation** from Git commit history
- 🤖 **AI-powered enhancement** with multiple provider support (Ollama, XAI, Anthropic)
- 📝 **Multiple output formats**: Markdown, HTML, and JSON
- 🎯 **Smart CLI interface** - works without subcommands
- 🔧 **Auto-configuration** - creates config files on first run
- 🔍 **Advanced filtering** - custom commit ranges and branch selection
- 📁 **Flexible output** - timestamped files or custom naming
- 🛡️ **Robust validation** - comprehensive error handling and tips
- 🎨 **Beautiful templates** - professional HTML and Markdown outputs
- 🔄 **Modular architecture** - easy to extend with new providers

## 🚀 Quick Start

### Installation

```bash
pip install changelog-generator
```

### Generate Your First Changelog

```bash
# Navigate to your Git repository
cd your-git-repo

# Generate changelog (creates config on first run)
changelog-generator

# Or specify output format
changelog-generator --output changelog.html  # HTML format
changelog-generator --output changelog.json  # JSON format
```

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

## 📖 Usage Examples

### Basic Usage

```bash
# Generate changelog in current directory
changelog-generator

# Generate for specific repository
changelog-generator --repo /path/to/repo

# Generate for specific branch
changelog-generator --branch develop

# Generate for specific commit range
changelog-generator --commit-range "abc123..def456"

# Use custom config file
changelog-generator --config my-config.yaml

# Enable verbose logging
changelog-generator --verbose
```

### Output Format Examples

```bash
# Generate HTML changelog
changelog-generator --output changelog.html

# Generate JSON changelog for API consumption
changelog-generator --output changelog.json

# Generate with custom filename
changelog-generator --output "release-v2.0.md"
```

### Advanced Examples

```bash
# Initialize configuration file
changelog-generator init

# List available AI models
changelog-generator models

# Generate changelog between two specific commits
changelog-generator abc123 def456

# Generate with specific AI provider
changelog-generator --model-provider anthropic --model-name claude-3-opus-20240229
```

## ⚙️ Configuration

The tool automatically creates a `.changelog.yaml` configuration file on first run. You can customize it:

```yaml
# Git Repository Settings
git:
  repository_path: .
  branch: main
  # commit_range: 'old_commit..new_commit'  # Optional

# Changelog Generation Settings  
changelog:
  output_file: "CHANGELOG.md"
  template: "markdown_template.j2"
  sections:
    - type: feat
      title: "🚀 Features"
    - type: fix
      title: "🐛 Bug Fixes"
    - type: docs
      title: "📝 Documentation"

# AI-Powered Generation
ai:
  enabled: true
  provider: ollama  # ollama, xai, or anthropic
  model_name: qwen3:latest
  
  # Provider-specific models
  ollama_model: qwen3:latest
  xai_model: grok-2
  anthropic_model: claude-3-opus-20240229
  
  # API keys (optional - can use environment variables)
  # xai_api_key: your_key_here
  # anthropic_api_key: your_key_here

# Breaking Change Detection
breaking_change_detection:
  keywords:
    - "breaking"
    - "breaking change" 
    - "deprecated"
    - "removed"

# Logging
logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR
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
- `provider`: AI provider (ollama, xai, or anthropic)
- `model_name`: Specific AI model to use

### Logging Settings

- `level`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)

## 🤖 AI Provider Setup

### Ollama (Local AI)
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve

# Pull a model
ollama pull qwen3:latest

# Configure in .changelog.yaml
ai:
  provider: ollama
  ollama_model: qwen3:latest
```

### XAI (Grok)
```bash
# Set API key
export XAI_API_KEY="your-xai-api-key"

# Or in .changelog.yaml
ai:
  provider: xai
  xai_model: grok-2
  xai_api_key: your-xai-api-key
```

### Anthropic (Claude)
```bash
# Set API key
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Or in .changelog.yaml
ai:
  provider: anthropic
  anthropic_model: claude-3-opus-20240229
  anthropic_api_key: your-anthropic-api-key
```

## 🎨 Output Formats

### Markdown (Default)
Standard markdown format suitable for GitHub, GitLab, and documentation sites.

### HTML
Beautiful, styled HTML with:
- Responsive design
- Syntax highlighting for commit hashes
- Collapsible sections
- Professional styling

### JSON
Machine-readable format perfect for:
- API integrations
- Custom processing
- Data analysis
- CI/CD pipelines

```json
{
  "metadata": {
    "commit_range": "abc123..def456",
    "generated_at": "2024-01-15T10:30:00",
    "total_commits": 42
  },
  "ai_summary": "Added user authentication and fixed critical bugs",
  "breaking_changes": ["Removed deprecated API endpoints"],
  "changes": {
    "feat": {
      "auth": [{"description": "Add OAuth2 support", "hash": "abc123"}]
    }
  }
}
```

## 🚨 Troubleshooting

### Common Issues

#### Git Repository Issues
```bash
# Error: Not a git repository
cd your-git-repo

# Error: No commits found
git commit -m "Initial commit"

# Error: Branch not found
git checkout -b main  # or your default branch
```

#### AI Provider Issues
```bash
# Ollama not running
ollama serve

# Missing model
ollama pull qwen3:latest

# Check available models
changelog-generator models

# API key issues
export XAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
```

#### Configuration Issues
```bash
# Create config file
changelog-generator init

# Validate configuration
changelog-generator --verbose

# Use custom config
changelog-generator --config path/to/config.yaml
```

### Debug Mode
```bash
# Enable verbose logging
changelog-generator --verbose

# Check configuration loading
changelog-generator --verbose --config .changelog.yaml
```

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
