import argparse
import git
import os
import sys
from typing import Dict, List
from dotenv import load_dotenv

# LLM and Langchain imports
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Local imports
from changelog_utils import validate_commits, get_commit_changes

# Load environment variables
load_dotenv()

def generate_ai_changelog(changes: Dict[str, List[str]]) -> str:
    """
    Generate a changelog using an AI model.
    
    Args:
        changes (dict): Detailed changes between commits
    
    Returns:
        str: AI-generated changelog
    """
    # Initialize the OpenAI language model
    llm = ChatOpenAI(
        model="gpt-4-turbo", 
        temperature=0.3, 
        max_tokens=500
    )
    
    # Create a prompt template for changelog generation
    changelog_prompt = PromptTemplate(
        input_variables=[
            'added_files', 
            'modified_files', 
            'deleted_files', 
            'commit_messages'
        ],
        template="""
        Generate a professional and concise changelog based on the following commit information:

        Added Files:
        {added_files}

        Modified Files:
        {modified_files}

        Deleted Files:
        {deleted_files}

        Commit Messages:
        {commit_messages}

        Provide a structured changelog that highlights key changes, improvements, and any potential breaking changes.
        Use markdown formatting and categorize changes if possible.
        """
    )
    
    # Create the LLM chain
    changelog_chain = LLMChain(llm=llm, prompt=changelog_prompt)
    
    # Generate the changelog
    changelog = changelog_chain.run(
        added_files='\n'.join(changes['added_files']) or 'No new files',
        modified_files='\n'.join(changes['modified_files']) or 'No files modified',
        deleted_files='\n'.join(changes['deleted_files']) or 'No files deleted',
        commit_messages='\n'.join(changes['commit_messages']) or 'No commit messages'
    )
    
    return changelog

def main():
    parser = argparse.ArgumentParser(description='Generate a detailed AI-powered changelog between two Git commits.')
    parser.add_argument('commit1', help='First commit hash or reference')
    parser.add_argument('commit2', help='Second commit hash or reference')
    parser.add_argument('--repo', default='.', help='Path to the Git repository (default: current directory)')
    parser.add_argument('--output', '-o', default='CHANGELOG.md', 
                        help='Output file for the generated changelog (default: CHANGELOG.md)')
    
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
        ai_changelog = generate_ai_changelog(changes)
        
        # Write changelog to file
        with open(args.output, 'w') as f:
            f.write(f"# Changelog: {commit1.hexsha[:7]}..{commit2.hexsha[:7]}\n\n")
            f.write(ai_changelog)
        
        print(f"Changelog generated and saved to {args.output}")
        print("\nChangelog Preview:")
        print(ai_changelog)
    
    except Exception as e:
        print(f"Error generating AI changelog: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
