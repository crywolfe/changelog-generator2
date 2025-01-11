import git
import sys
import re
from typing import Dict, List, Union
import spacy
import semantic_version

def validate_commits(repo, commit1, commit2):
    """
    Validate that both commits exist in the repository.

    Args:
        repo (git.Repo): Git repository object
        commit1 (str): First commit hash or reference
        commit2 (str): Second commit hash or reference

    Returns:
        tuple: Validated commit objects

    Raises:
        SystemExit: If either commit is invalid.
    """
    try:
        return repo.commit(commit1), repo.commit(commit2)
    except git.exc.BadName as e:
        print(f"Error: Invalid commit reference - {e}. Commits ({commit1}, {commit2}) do not exist in the repository.")
        sys.exit(1)


def get_commit_changes_modified(repo: git.Repo, commit1: Union[str, git.Commit], commit2: Union[str, git.Commit]) -> List[str]:
    """
    Retrieve modified files between two commits.

    Args:
        repo (git.Repo): Git repository object
        commit1 (str or git.Commit): First commit
        commit2 (str or git.Commit): Second commit

    Returns:
        list: List of modified files
    """
    commit1 = repo.commit(commit1) if isinstance(commit1, str) else commit1
    commit2 = repo.commit(commit2) if isinstance(commit2, str) else commit2

    diff = commit1.diff(commit2)
    return [change.b_path for change in diff if change.change_type == "M"]


def format_breaking_changes(breaking_changes: List[str]) -> str:
    """
    Format breaking changes into a readable string.

    Args:
        breaking_changes (List[str]): List of breaking change messages

    Returns:
        str: Formatted breaking changes
    """
    return "- No breaking changes" if not breaking_changes else "\n".join([f"- {change}" for change in breaking_changes])


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
    commit1 = repo.commit(commit1) if isinstance(commit1, str) else commit1
    commit2 = repo.commit(commit2) if isinstance(commit2, str) else commit2

    diff = commit1.diff(commit2)
    changes = {
        "added_files": [],
        "modified_files": [],
        "deleted_files": [],
        "commit_messages": [],
        "diff_details": [],
        "breaking_changes": [],
    }

    for change in diff:
        if change.change_type == "A":
            changes["added_files"].append(change.b_path)
        elif change.change_type == "M":
            changes["modified_files"].append(change.b_path)
            try:
                patch = change.diff if isinstance(change.diff, str) else change.diff.decode("utf-8")
                changes["diff_details"].append({"file": change.b_path, "patch": patch})
            except Exception as e:
                print(f"Could not process diff for {change.b_path}: {e}")
        elif change.change_type == "D":
            changes["deleted_files"].append(change.b_path)

    changes["commit_messages"] = [commit2.message.strip()]

    # Detect breaking changes
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        print("Downloading spaCy language model...")
        spacy.cli.download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")

    def detect_breaking_changes(message):
        message_lower = message.lower()
        breaking_keywords = [
            "breaking", "breaking change", "deprecated", "removed", "breaking api",
            "breaking interface", "major version", "incompatible", "refactored", "restructured",
            "breaking change:", "breaking changes:", "breaking modification:", "significant change:",
            "non-backward compatible", "api modification",
        ]

        if any(keyword in message_lower or message_lower.startswith(keyword) or keyword in message_lower.split() for keyword in breaking_keywords):
            return True

        try:
            version_match = re.search(r"v?(\d+\.\d+\.\d+)", message)
            if version_match and semantic_version.Version(version_match.group(1)).major > 0:
                return True
        except ValueError:
            pass

        doc = nlp(message)
        for sent in doc.sents:
            for token in sent:
                if token.pos_ == "VERB" and token.lemma_ in ["remove", "deprecate", "refactor", "restructure", "modify", "change"]:
                    return True

        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT", "WORK_OF_ART"] and any(keyword in ent.text.lower() for keyword in ["api", "interface", "library"]):
                return True

        return False

    for message in changes["commit_messages"]:
        if detect_breaking_changes(message):
            changes["breaking_changes"].append(message)

    for diff_detail in changes.get("diff_details", []):
        if diff_detail.get("patch"):
            patch = diff_detail["patch"].lower()
            structural_changes = [
                "class renamed", "method signature changed", "interface modified",
                "function removed", "parameter type changed",
            ]
            if any(change in patch for change in structural_changes):
                changes["breaking_changes"].append(f"Structural change in {diff_detail.get('file', 'unknown file')}")

    return changes