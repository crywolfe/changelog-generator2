import git
import sys
import re
from typing import Dict, List, Union


def validate_commits(repo, commit1, commit2):
    """
    Validate that both commits exist in the repository.

    Args:
        repo (git.Repo): Git repository object
        commit1 (str): First commit hash or reference
        commit2 (str): Second commit hash or reference

    Returns:
        tuple: Validated commit objects
    """
    try:
        c1 = repo.commit(commit1)
        c2 = repo.commit(commit2)
        return c1, c2
    # do you like this exception logic. AI!
    except git.exc.BadName:
        print(
            f"Error: One or both commits ({commit1}, {commit2}) do not exist in the repository."
        )
        sys.exit(1)


def get_commit_changes_modified(
    repo: git.Repo, commit1: Union[str, git.Commit], commit2: Union[str, git.Commit]
) -> List[str]:
    """
    Retrieve modified files between two commits.

    Args:
        repo (git.Repo): Git repository object
        commit1 (str or git.Commit): First commit
        commit2 (str or git.Commit): Second commit

    Returns:
        list: List of modified files
    """
    # Convert commit references to commit objects if they are strings
    if isinstance(commit1, str):
        commit1 = repo.commit(commit1)
    if isinstance(commit2, str):
        commit2 = repo.commit(commit2)

    # Get the diff between commits
    diff = commit1.diff(commit2)

    # Collect modified files
    modified_files = [change.b_path for change in diff if change.change_type == "M"]

    return modified_files


def format_breaking_changes(breaking_changes: List[str]) -> str:
    """
    Format breaking changes into a readable string.

    Args:
        breaking_changes (List[str]): List of breaking change messages

    Returns:
        str: Formatted breaking changes
    """
    if not breaking_changes:
        return "- No breaking changes"

    return "\n".join([f"- {change}" for change in breaking_changes])


def get_commit_changes(repo, commit1, commit2) -> Dict[str, List[str]]:
    """
    Retrieve changes between two commits.

    Args:
        repo (git.Repo): Git repository object
        commit1 (git.Commit): First commit
        commit2 (git.Commit): Second commit

    Returns:
        dict: Detailed changes between commits
    """
    # Convert commit references to commit objects if they are strings
    if isinstance(commit1, str):
        commit1 = repo.commit(commit1)
    if isinstance(commit2, str):
        commit2 = repo.commit(commit2)

    diff = commit1.diff(commit2)

    changes = {
        "added_files": [],
        "modified_files": [],
        "deleted_files": [],
        "commit_messages": [],
        "diff_details": [],
        "breaking_changes": [],  # New section for breaking changes
    }

    for change in diff:
        if change.change_type == "A":
            changes["added_files"].append(change.b_path)
        elif change.change_type == "M":
            changes["modified_files"].append(change.b_path)
            # Get more detailed diff information
            try:
                patch = (
                    change.diff
                    if isinstance(change.diff, str)
                    else change.diff.decode("utf-8")
                )
                changes["diff_details"].append({"file": change.b_path, "patch": patch})
            except Exception as e:
                print(f"Could not process diff for {change.b_path}: {e}")
        elif change.change_type == "D":
            changes["deleted_files"].append(change.b_path)

    # Collect only the commit message for the last commit in the range
    changes["commit_messages"] = [commit2.message.strip()]

    # Detect breaking changes
    import spacy
    import semantic_version

    # Load spaCy model for advanced NLP
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        print("Downloading spaCy language model...")
        spacy.cli.download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")

    breaking_keywords = [
        "breaking",
        "breaking change",
        "deprecated",
        "removed",
        "breaking api",
        "breaking interface",
        "major version",
        "incompatible",
        "refactored",
        "restructured",
    ]

    def detect_breaking_changes(message):
        """
        Advanced detection of breaking changes using NLP and semantic analysis.
        
        Args:
            message (str): Commit message to analyze

        Returns:
            bool: True if the message indicates a breaking change, False otherwise
        """
        # Convert message to lowercase for case-insensitive matching
        message_lower = message.lower()

        # Expanded breaking change keywords
        breaking_keywords = [
            "breaking",
            "breaking change",
            "deprecated",
            "removed",
            "breaking api",
            "breaking interface",
            "major version",
            "incompatible",
            "refactored",
            "restructured",
            "breaking change:",
            "breaking changes:",
            "breaking modification:",
            "significant change:",
            "non-backward compatible",
            "api modification",
        ]

        # Keyword-based detection with more comprehensive matching
        if any(
            keyword in message_lower or 
            message_lower.startswith(keyword) or 
            keyword in message_lower.split()
            for keyword in breaking_keywords
        ):
            return True

        # Semantic version detection in commit messages
        try:
            version_match = re.search(r"v?(\d+\.\d+\.\d+)", message)
            if version_match:
                version = semantic_version.Version(version_match.group(1))
                if version.major > 0 or version.minor > 0:  # Major or minor version change
                    return True
        except ValueError:
            pass

        # NLP-based semantic analysis with more context
        doc = nlp(message)
        
        # Check for specific linguistic patterns indicating breaking changes
        for sent in doc.sents:
            # Look for verbs that might indicate significant changes
            for token in sent:
                if token.pos_ == "VERB" and token.lemma_ in [
                    "remove", 
                    "deprecate", 
                    "refactor", 
                    "restructure", 
                    "modify", 
                    "change"
                ]:
                    return True

        # Check for named entities that might indicate API or interface changes
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT", "WORK_OF_ART"] and any(
                keyword in ent.text.lower() for keyword in ["api", "interface", "library"]
            ):
                return True

        return False

    # Collect breaking changes from commit messages
    for message in changes["commit_messages"]:
        if detect_breaking_changes(message):
            changes["breaking_changes"].append(message)
    
    # Additional breaking changes detection from diff details
    for diff_detail in changes.get("diff_details", []):
        # Check if significant structural changes are present
        if diff_detail.get("patch"):
            patch = diff_detail["patch"].lower()
            structural_changes = [
                "class renamed",
                "method signature changed",
                "interface modified",
                "function removed",
                "parameter type changed",
            ]
            
            if any(change in patch for change in structural_changes):
                changes["breaking_changes"].append(
                    f"Structural change in {diff_detail.get('file', 'unknown file')}"
                )

    return changes
