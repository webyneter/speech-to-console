#!/usr/bin/env python3
"""
Script to automatically generate CHANGELOG entries from git commit history.
Extracts commits since the last release and categorizes them.
"""

import argparse
import re
import subprocess
from datetime import datetime


def get_last_tag():
    """Get the most recent tag from git history"""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        # No tags found
        return None


def get_commits_since_tag(tag):
    """Get all commits since the specified tag"""
    if tag:
        cmd = ["git", "log", f"{tag}..HEAD", "--pretty=format:%s"]
    else:
        # No tag found, get all commits
        cmd = ["git", "log", "--pretty=format:%s"]
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip().split("\n")


def categorize_commit(commit):
    """Categorize commit based on its message"""
    commit = commit.strip()
    if not commit:
        return None, None
    
    # Define patterns for different types of commits
    patterns = {
        "Added": [r"^add", r"^feat", r"^new", r"^implement"],
        "Fixed": [r"^fix", r"^bugfix", r"^hotfix", r"^resolve"],
        "Changed": [r"^change", r"^update", r"^modify", r"^improve", r"^enhance", r"^refactor"],
        "Removed": [r"^remove", r"^delete", r"^deprecate"],
        "Security": [r"^security"],
        "Documentation": [r"^doc"],
        "Tests": [r"^test"],
        "Dependencies": [r"^bump", r"^upgrade", r"^update.*dependenc"]
    }
    
    # Check each category
    for category, patterns_list in patterns.items():
        for pattern in patterns_list:
            if re.search(pattern, commit.lower()):
                # Clean up commit message for changelog
                # Remove common prefixes like "fix:", "feat:", etc.
                clean_msg = re.sub(r"^(fix|feat|feature|chore|refactor|style|test|docs|build|ci)(\(.*?\))?:\s*", "", commit)
                # Capitalize first letter
                clean_msg = clean_msg[0].upper() + clean_msg[1:] if clean_msg else commit
                return category, clean_msg
    
    # Default category for other commits
    return "Changed", commit


def update_changelog(commits_by_category):
    """Update the CHANGELOG.md file with new entries"""
    try:
        with open("CHANGELOG.md", "r") as f:
            content = f.read()
    except FileNotFoundError:
        # Create a new changelog if it doesn't exist
        content = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"""

    # Find the Unreleased section or create it
    if "## [Unreleased]" not in content:
        content = content.replace("# Changelog", "# Changelog\n\n## [Unreleased]")

    # Generate entries for each category
    new_entries = ""
    for category, commits in commits_by_category.items():
        if commits:
            new_entries += f"\n### {category}\n"
            for commit in commits:
                new_entries += f"- {commit}\n"

    # Insert new entries after the Unreleased header
    if new_entries:
        if "## [Unreleased]\n\n## [" in content:
            # There's already a version section, insert between Unreleased and first version
            content = content.replace("## [Unreleased]\n", f"## [Unreleased]\n{new_entries}\n")
        else:
            # No version section yet
            content = content.replace("## [Unreleased]", f"## [Unreleased]{new_entries}")

    # Write the updated content back
    with open("CHANGELOG.md", "w") as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(description="Generate CHANGELOG entries from git commits")
    parser.add_argument("--dry-run", action="store_true", help="Print changelog entries without updating the file")
    args = parser.parse_args()

    last_tag = get_last_tag()
    print(f"Last tag found: {last_tag or 'None'}")
    
    commits = get_commits_since_tag(last_tag)
    if not commits or (len(commits) == 1 and not commits[0]):
        print("No new commits found since the last tag.")
        return
    
    # Categorize commits
    commits_by_category = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
        "Security": [],
        "Documentation": [],
        "Tests": [],
        "Dependencies": []
    }
    
    for commit in commits:
        category, message = categorize_commit(commit)
        if category:
            commits_by_category[category].append(message)
    
    # Remove empty categories
    commits_by_category = {k: v for k, v in commits_by_category.items() if v}
    
    if args.dry_run:
        print("\nGenerated CHANGELOG entries:")
        for category, commits in commits_by_category.items():
            print(f"\n### {category}")
            for commit in commits:
                print(f"- {commit}")
    else:
        update_changelog(commits_by_category)
        print("\nCHANGELOG.md has been updated with new entries.")


if __name__ == "__main__":
    main()