# Git Changelog Generator

## Overview

This Python script generates a detailed changelog between two Git commits, helping you track changes in your repository.

## Prerequisites

- Python 3.7+
- GitPython library
- OpenAI API Key
- Langchain
- python-dotenv
- Ollama Client

## Installation

### Prerequisites

1. **Ollama Client:**
   - Ensure that the Ollama client is installed on your system. You can install it using pip:

     ```bash
     pip install ollama
     ```

2. **Python Packages:**

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Alternatively, you can install the dependencies individually:

```bash
pip install GitPython langchain-openai langchain-community python-dotenv ollama
```

3. **Optional: Set up Ollama**

```bash
# Install Ollama from https://ollama.com/
# Pull a model, e.g.:
ollama pull llama2
```

4. **Set up OpenAI API Key (if using OpenAI):**

There are two ways to configure your OpenAI API key:

a. **Using a `.env` file (Recommended):**

```bash
# Create a .env file in your project directory
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

b. **Using an environment variable:**

```bash
# Set the OpenAI API key in your shell
export CHANGELOG_OPENAI_API_KEY=your_openai_api_key_here

# Or set it inline when running the script
CHANGELOG_OPENAI_API_KEY=your_openai_api_key_here changelog-generator HEAD~1 HEAD --model-provider openai
```

Note: You can obtain an API key from the [OpenAI Platform](https://platform.openai.com/api-keys).
Always keep your API key confidential and never commit it to version control.

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

5. **Use Ollama or OpenAI with a specific model:**

```bash
# Ollama model selection
changelog-generator HEAD~1 HEAD --model-provider ollama --model-name llama2

# OpenAI model selection
changelog-generator HEAD~1 HEAD --model-provider openai --model-name gpt-4-turbo
```

Available AI models:

- **OpenAI models:**
  - `gpt-4`
  - `gpt-4-turbo`
  - `gpt-3.5-turbo`

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
changelog-generator HEAD~1 HEAD --model-provider xai --model-name grok-1
```

## Arguments

- `commit1`: First commit hash or reference
- `commit2`: Second commit hash or reference
- `--repo`: Optional path to the Git repository (default is current directory)
- `--model-provider`: AI model provider (openai, ollama, or xai, default is ollama)
- `--model-name`: Specific model to use (default: qwen2.5:14b for Ollama, gpt-4-turbo for OpenAI)
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

[Specify your license here]
