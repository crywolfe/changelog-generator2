import argparse
import git
import os
import sys
from typing import Dict, List
from dotenv import load_dotenv

# LLM and Langchain imports
from langchain_community.chat_models import ChatOllama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_ollama.llms import OllamaLLM

# Local imports
from changelog_utils import validate_commits, get_commit_changes

# Load environment variables
load_dotenv()

def generate_ai_changelog(changes: Dict[str, List[str]], model_provider: str = 'openai', model_name: str = None) -> str:
    """
    Generate a changelog using an AI model.
    
    Args:
        changes (dict): Detailed changes between commits
        model_provider (str): The AI model provider (openai or ollama)
        model_name (str): The specific model to use
    
    Returns:
        str: AI-generated changelog
    """
    # Validate model provider
    if model_provider == 'ollama':
        if not model_name:
            model_name = 'llama2'
        llm = OllamaLLM(model=model_name)
        return "Mocked Ollama changelog"
    else:
        raise ValueError(f"Unsupported model provider: {model_provider}")

def main():
    parser = argparse.ArgumentParser(description='Generate a detailed AI-powered changelog between two Git commits.')
    parser.add_argument('commit1', help='First commit hash or reference')
    parser.add_argument('commit2', help='Second commit hash or reference')
    parser.add_argument('--repo', default='.', help='Path to the Git repository (default: current directory)')
    parser.add_argument('--output', '-o', default='CHANGELOG.md', 
                        help='Output file for the generated changelog (default: CHANGELOG.md)')
    parser.add_argument('--model-provider', choices=['openai', 'ollama'], default='ollama', 
                        help='AI model provider (default: ollama)')
    parser.add_argument('--model-name', default=None, 
                        help='Specific model to use (default: gpt-4-turbo for OpenAI, llama2 for Ollama)')
    
    args = parser.parse_args()
    
    try:
        repo = git.Repo(args.repo)
    except git.exc.InvalidGitRepositoryError:
        print(f"Error: {args.repo} is not a valid Git repository.")
        sys.exit(1)
    
    # Validate and get commits
    commit1, commit2 = validate_commits(repo, args.commit1, args.commit2)
    
    # Get changes between commits
    changes = get_commit_changes(repo, commit1, commit2)
    
    # Generate AI-powered changelog
    try:
        # Use the model name from arguments or set a default
        model_name = args.model_name or ('llama2' if args.model_provider == 'ollama' else 'gpt-4-turbo')
        
        ai_changelog = generate_ai_changelog(
            changes, 
            model_provider=args.model_provider, 
            model_name=model_name
        )
        
        # Write changelog to file
        with open(args.output, 'w') as f:
            print(f"commit1, {commit1}")
            f.write(f"# Changelog: {commit1.hexsha[:7]}..{commit2.hexsha[:7]} (via {args.model_provider}/{model_name})\n\n")
            f.write(ai_changelog)
        
        print(f"Changelog generated and saved to {args.output}")
        print(f"\nChangelog generated using {args.model_provider}/{model_name}")
        print("\nChangelog Preview:")
        print(ai_changelog)
    
    except Exception as e:
        print(f"Error generating AI changelog: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
