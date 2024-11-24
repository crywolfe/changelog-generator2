import argparse
import git
import sys
from typing import Dict, List
from dotenv import load_dotenv
import ollama

# Local imports
from changelog_utils import validate_commits, get_commit_changes, format_breaking_changes

# Load environment variables
load_dotenv()

class OllamaLLM:
    def __init__(self, model='llama2'):
        self.model = model
    
    def _create_changelog_prompt(self, changes: Dict[str, List[str]]) -> str:
        """
        Create a detailed prompt for changelog generation.
        
        Args:
            changes (dict): Detailed changes between commits
        
        Returns:
            str: Formatted prompt for LLM
        """
        prompt = "Generate a comprehensive changelog based on the following commit changes:\n\n"
        
        # Added Files
        if changes['added_files']:
            prompt += "New Files Added:\n"
            for file in changes['added_files']:
                prompt += f"- {file}\n"
        
        # Modified Files
        if changes['modified_files']:
            prompt += "\nModified Files:\n"
            for file in changes['modified_files']:
                prompt += f"- {file}\n"
        
        # Deleted Files
        if changes['deleted_files']:
            prompt += "\nDeleted Files:\n"
            for file in changes['deleted_files']:
                prompt += f"- {file}\n"
        
        # Breaking Changes
        if changes['breaking_changes']:
            prompt += "\nBreaking Changes:\n"
            for change in changes['breaking_changes']:
                prompt += f"- {change}\n"
        
        # Commit Messages
        if changes['commit_messages']:
            prompt += "\nCommit Messages:\n"
            for msg in changes['commit_messages']:
                prompt += f"- {msg}\n"
        
        prompt += "\nPlease generate a detailed, professional changelog that highlights key changes, " \
                  "new features, bug fixes, and any breaking changes. Use markdown formatting."
        
        return prompt
    
    def invoke(self, changes: Dict[str, List[str]]) -> str:
        """
        Generate changelog using Ollama LLM.
        
        Args:
            changes (dict): Detailed changes between commits
        
        Returns:
            str: Generated changelog
        """
        try:
            prompt = self._create_changelog_prompt(changes)
            
            response = ollama.chat(model=self.model, messages=[
                {'role': 'system', 'content': 'You are a professional software changelog generator.'},
                {'role': 'user', 'content': prompt}
            ])
            
            return response['message']['content']
        
        except Exception as e:
            print(f"Error generating changelog with Ollama: {e}")
            return f"Unable to generate changelog. Error: {e}"

def generate_ai_changelog(changes: Dict[str, List[str]], model_provider: str = 'ollama', model_name: str = None) -> str:
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
        
        # Create Ollama LLM instance
        ollama_llm = OllamaLLM(model=model_name)
        return ollama_llm.invoke(changes)
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
    parser.add_argument('--verbose', '-v', action='store_true', 
                        help='Enable verbose logging')
    
    args = parser.parse_args()
    
    try:
        repo = git.Repo(args.repo)
    except git.exc.InvalidGitRepositoryError:
        print(f"Error: {args.repo} is not a valid Git repository.")
        sys.exit(1)
    
    # Validate and get commits
    try:
        commit1, commit2 = validate_commits(repo, args.commit1, args.commit2)
    except Exception as e:
        print(f"Commit validation error: {e}")
        sys.exit(1)
    
    # Get changes between commits
    try:
        changes = get_commit_changes(repo, commit1, commit2)
        
        if args.verbose:
            print("Detected Changes:")
            print(f"Added Files: {changes['added_files']}")
            print(f"Modified Files: {changes['modified_files']}")
            print(f"Deleted Files: {changes['deleted_files']}")
            print(f"Breaking Changes: {changes['breaking_changes']}")
    except Exception as e:
        print(f"Error retrieving commit changes: {e}")
        sys.exit(1)
    
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
            f.write(f"# Changelog: {commit1.hexsha[:7]}..{commit2.hexsha[:7]} (via {args.model_provider}/{model_name})\n\n")
            f.write(ai_changelog)
        
        print(f"Changelog generated and saved to {args.output}")
        print(f"\nChangelog generated using {args.model_provider}/{model_name}")
        
        if args.verbose:
            print("\nChangelog Preview:")
            print(ai_changelog)
    
    except Exception as e:
        print(f"Error generating AI changelog: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
