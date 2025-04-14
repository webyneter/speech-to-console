#!/usr/bin/env python3
"""
Script to automate the entire release process for speech-to-console.
Generates changelog from commits, updates version in pyproject.toml,
commits changes, and creates a git tag.
"""

import argparse
import os
import re
import subprocess
from datetime import date

import tomli
import tomli_w


def read_toml(file_path):
    """Read TOML file"""
    with open(file_path, "rb") as f:
        return tomli.load(f)


def write_toml(file_path, data):
    """Write TOML file"""
    with open(file_path, "wb") as f:
        tomli_w.dump(data, f)


def update_pyproject_version(pyproject_path, new_version):
    """Update version in pyproject.toml"""
    data = read_toml(pyproject_path)
    old_version = data["project"]["version"]
    data["project"]["version"] = new_version
    write_toml(pyproject_path, data)
    return old_version


def update_init_version(repo_root, new_version):
    """Update version in __init__.py"""
    init_path = os.path.join(repo_root, "speech_to_console", "__init__.py")

    if not os.path.exists(init_path):
        print(f"Warning: Could not find {init_path}")
        return False

    with open(init_path, "r") as f:
        content = f.read()

    # Replace version string
    new_content = re.sub(
        r'__version__ = "[^"]+"', f'__version__ = "{new_version}"', content
    )

    with open(init_path, "w") as f:
        f.write(new_content)

    print(f"Updated version in {init_path}")
    return True


def get_last_tag():
    """Get the most recent tag from git history"""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=True,
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
        "Changed": [
            r"^change",
            r"^update",
            r"^modify",
            r"^improve",
            r"^enhance",
            r"^refactor",
        ],
        "Removed": [r"^remove", r"^delete", r"^deprecate"],
        "Security": [r"^security"],
        "Documentation": [r"^doc"],
        "Tests": [r"^test"],
        "Dependencies": [r"^bump", r"^upgrade", r"^update.*dependenc"],
    }

    # Check each category
    for category, patterns_list in patterns.items():
        for pattern in patterns_list:
            if re.search(pattern, commit.lower()):
                # Clean up commit message for changelog
                # Remove common prefixes like "fix:", "feat:", etc.
                clean_msg = re.sub(
                    r"^(fix|feat|feature|chore|refactor|style|test|docs|build|ci)(\(.*?\))?:\s*",
                    "",
                    commit,
                )
                # Capitalize first letter
                clean_msg = (
                    clean_msg[0].upper() + clean_msg[1:] if clean_msg else commit
                )
                return category, clean_msg

    # Default category for other commits
    return "Changed", commit


def generate_changelog(changelog_path, new_version):
    """Generate changelog entries from git commits and update the file"""
    today = date.today().strftime("%Y-%m-%d")
    last_tag = get_last_tag()
    print(f"Last tag found: {last_tag or 'None'}")

    commits = get_commits_since_tag(last_tag)
    if not commits or (len(commits) == 1 and not commits[0]):
        print("No new commits found since the last tag.")
        return False

    # Categorize commits
    commits_by_category = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
        "Security": [],
        "Documentation": [],
        "Tests": [],
        "Dependencies": [],
    }

    for commit in commits:
        category, message = categorize_commit(commit)
        if category:
            commits_by_category[category].append(message)

    # Remove empty categories
    commits_by_category = {k: v for k, v in commits_by_category.items() if v}

    if not commits_by_category:
        print("No categorized commits found.")
        return False

    try:
        with open(changelog_path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        # Create a new changelog if it doesn't exist
        content = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
"""

    # Generate entries
    entries = f"\n## [{new_version}] - {today}\n"
    for category, commits in commits_by_category.items():
        if commits:
            entries += f"\n### {category}\n"
            for commit in commits:
                entries += f"- {commit}\n"

    # Insert after Unreleased section
    if "## [Unreleased]" in content:
        content = content.replace("## [Unreleased]", "## [Unreleased]\n" + entries)
    else:
        # Fallback if Unreleased section not found
        content = content + "\n" + entries

    # Update version links at the bottom
    old_version = last_tag.lstrip("v") if last_tag else "0.0.0"

    # Extract existing links section if it exists
    links_match = re.search(r"\n\[.*\]: .*", content, re.DOTALL)
    if links_match:
        links_section = links_match.group(0)
        # Remove old links section
        content = content.replace(links_section, "")
    else:
        links_section = ""

    # Create new links section
    new_links = f"""
[Unreleased]: https://github.com/webyneter/speech-to-console/compare/v{new_version}...HEAD
[{new_version}]: https://github.com/webyneter/speech-to-console/compare/v{old_version}...v{new_version}"""

    # Add existing version links
    if links_section:
        # Extract all version links
        version_links = re.findall(r"\[(\d+\.\d+\.\d+)\]: (.*)", links_section)
        for version, url in version_links:
            if version != new_version and version != "Unreleased":
                new_links += f"\n[{version}]: {url}"

    content += new_links

    # Write updated content back
    with open(changelog_path, "w") as f:
        f.write(content)

    print(f"CHANGELOG.md updated with entries for version {new_version}")
    return True


def update_lockfile(repo_root):
    """Update the uv.lock file"""
    print("Updating uv.lock file...")
    try:
        result = subprocess.run(
            ["uv", "lock"], cwd=repo_root, capture_output=True, text=True, check=True
        )
        print(result.stdout.strip())
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error updating lockfile: {e}")
        print(e.stderr)
        return False


def git_commands(new_version, files_to_commit):
    """Run git commands to commit changes and create a tag"""
    # First add all the files
    add_cmd = ["git", "add"] + files_to_commit
    subprocess.run(add_cmd, check=True)

    # Try to commit
    try:
        commit_cmd = ["git", "commit", "-m", f"Release v{new_version}"]
        subprocess.run(commit_cmd, check=True)
    except subprocess.CalledProcessError:
        # Pre-commit hooks might have modified files
        print("Commit failed. Pre-commit hooks modified files. Trying again...")
        add_cmd = ["git", "add", "."]  # Add all changes
        subprocess.run(add_cmd, check=True)

        commit_cmd = ["git", "commit", "-m", f"Release v{new_version}"]
        subprocess.run(commit_cmd, check=True)

    # Create the tag
    tag_cmd = ["git", "tag", "-a", f"v{new_version}", "-m", f"Release v{new_version}"]
    subprocess.run(tag_cmd, check=True)

    print(f"Changes committed and tag v{new_version} created")
    print("\nTo push changes and trigger a release, run:")
    print(f"  git push && git push origin v{new_version}")
    print("\nNOTE: The release workflow will only run if the build workflow succeeds.")


def main():
    parser = argparse.ArgumentParser(
        description="Automate release process with changelog and version updates"
    )
    parser.add_argument("version", help="New version to release (e.g. 0.2.3)")
    parser.add_argument(
        "--no-git", action="store_true", help="Skip git commit and tag creation"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    # Get repository root
    repo_root = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    pyproject_path = os.path.join(repo_root, "pyproject.toml")
    changelog_path = os.path.join(repo_root, "CHANGELOG.md")

    # Read current version from pyproject.toml
    current_version = read_toml(pyproject_path)["project"]["version"]
    new_version = args.version

    print(f"Preparing release v{new_version} (current: {current_version})")

    if args.dry_run:
        print("\nDRY RUN: No changes will be made")
        print(f"Would update pyproject.toml version: {current_version} → {new_version}")
        print(f"Would update __init__.py version: {current_version} → {new_version}")
        print(f"Would generate changelog entries in {changelog_path}")
        print("Would update uv.lock file")
        print(f"Would commit changes and create tag v{new_version}")
        return

    # Update files
    update_pyproject_version(pyproject_path, new_version)
    update_init_version(repo_root, new_version)
    generate_changelog(changelog_path, new_version)
    update_lockfile(repo_root)

    init_path = os.path.join(repo_root, "speech_to_console", "__init__.py")
    lock_path = os.path.join(repo_root, "uv.lock")
    files_to_commit = [pyproject_path, changelog_path, init_path, lock_path]

    # Git operations
    if not args.no_git:
        git_commands(new_version, files_to_commit)


if __name__ == "__main__":
    main()
