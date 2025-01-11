## Configuration

The changelog generator can be configured using the `ChangelogConfig` class or environment variables. Here are the available configuration options:

### Configuration Class Options

- `model_provider`: The AI provider to use (default: "ollama")
  - Supported providers: "ollama", "xai"
- `model_name`: Optional specific model name
- `output_format`: Format of the generated changelog (default: "markdown")
- `output_directory`: Directory to save the changelog (default: current directory)
- `max_changelog_entries`: Maximum number of entries to include (default: 50)

### Environment Variable Configuration

For Ollama models, you can set the model using an environment variable:

- `OLLAMA_MODEL`: Specify the Ollama model to use
  - Example: `export OLLAMA_MODEL=llama3:latest`

### Examples

#### Using ChangelogConfig
```python
from changelog_config import ChangelogConfig

# Use a specific Ollama model
config = ChangelogConfig(
    model_provider="ollama", 
    model_name="qwen2.5:14b"
)

# Or use the default with environment variable configuration
config = ChangelogConfig(model_provider="ollama")
```

#### Environment Variable Configuration
```bash
# Set Ollama model via environment variable
export OLLAMA_MODEL=qwen2.5:14b
```

or use .env
To configure the application, create a `.env` file with the following variables:

```env
OLLAMA_MODEL=qwen2.5:14b
XAI_MODEL=grok-2
OUTPUT_FILE=CHANGELOG_DEFAULT.md
XAI_API_KEY=your_api_key_here
```
Make sure to replace `your_api_key_here` with your actual API key for `XAI_API_KEY`.

# Git Changelog Generator

## Overview

This Python script generates a detailed changelog between two Git commits, helping you track changes in your repository.

## Prerequisites

- Python 3.7+
- GitPython library
- Langchain Community
- python-dotenv
- Ollama

## Installation

1. **Ollama Client**
   - Ensure that the Ollama client is installed on your system. You can install it using pip:

     ```bash
     pip install ollama
     ```

2. **Python Packages**

Install the required Python packages:

```bash
pip install -r requirements.txt
```

1. **Optional: Set up Ollama**

```bash
# Install Ollama from https://ollama.com/
# Pull a model, e.g.:
ollama pull llama2
```

## Project Structure

- `changelog_generator.py`: Main script for generating changelogs
- `changelog_utils.py`: Utility functions for commit and repository operations

## Usage

### Basic Usage

Generate a changelog between two commits:

```bash
python changelog_generator.py <commit1> <commit2>
```

### Examples

1. **Compare the last 5 commits with the current HEAD:**

```bash
python changelog_generator.py HEAD~5 HEAD
```

2. **Compare specific commit hashes:**

```bash
python changelog_generator.py abc1234 def5678
```

3. **Specify a different repository path:**

```bash
python changelog_generator.py HEAD~3 HEAD --repo /path/to/your/repo
```

4. **Generate changelog with custom output file:**

```bash
python changelog_generator.py HEAD~1 HEAD -o MY_CHANGELOG.md
```

5. **Use Ollama or XAI with a specific model:**

```bash
# Ollama model selection
changelog-generator HEAD~1 HEAD --model-provider ollama --model-name llama2

# XAI model selection
changelog-generator HEAD~1 HEAD --model-provider xai --model-name grok-2
```

Available AI models:

- **Ollama models can be listed with:**

```bash
changelog-generator --list-models
```

- **XAI (Grok) models:**
  - `grok-1`

### XAI (Grok) Configuration

To use the XAI Grok model, set the `XAI_API_KEY` in your `.env` file:

```bash
echo "XAI_API_KEY=your_xai_api_key_here" >> .env
```

Example usage:

```bash
changelog-generator HEAD~1 HEAD --model-provider xai --model-name grok-2
```

## Arguments

- `commit1`: First commit hash or reference
- `commit2`: Second commit hash or reference
- `--repo`: Optional path to the Git repository (default is current directory)
- `--model-provider`: AI model provider (ollama or xai, default is ollama)
- `--model-name`: Specific model to use (default: qwen2.5:14b for Ollama)
- `--list-models`: List available Ollama models
- `--verbose`: Enable verbose logging

## Troubleshooting

- Ensure you're in a valid Git repository
- Verify commit references exist
- Check that GitPython is correctly installed

## Future Improvements

- Enhanced AI changelog generation
- Support for multiple LLM providers
- Customizable changelog templates
- Improved diff parsing and analysis

## License

[MIT License]

Copyright (c) 2025 Gerry Wolfe

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.