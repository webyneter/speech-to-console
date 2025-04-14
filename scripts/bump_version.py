#!/usr/bin/env python3
"""
Script to automate version bumping for speech-to-console.
Updates version in pyproject.toml, adds version section to CHANGELOG.md,
updates version links, commits the changes, and creates a git tag.
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


def update_changelog(changelog_path, new_version, old_version):
    """Update CHANGELOG.md with new version section and links"""
    today = date.today().strftime("%Y-%m-%d")
    
    with open(changelog_path, "r") as f:
        content = f.read()
    
    # Add new version section
    unreleased_pattern = r"## \[Unreleased\]\n\n(.*?)## \["
    unreleased_content = re.search(unreleased_pattern, content, re.DOTALL)
    
    if unreleased_content:
        unreleased_text = unreleased_content.group(1)
        # Only replace if there's actual content in unreleased section
        if unreleased_text.strip():
            # Replace unreleased section with new version
            new_content = re.sub(
                r"## \[Unreleased\]\n\n",
                f"## [Unreleased]\n\n## [{new_version}] - {today}\n\n",
                content, 
                1
            )
            
            # Update version links at the bottom
            link_pattern = r"\[Unreleased\]: .+\n"
            new_content = re.sub(
                link_pattern,
                f"[Unreleased]: https://github.com/webyneter/speech-to-console/compare/v{new_version}...HEAD\n",
                new_content
            )
            
            # Add new version link
            links_section = new_content.split("[Unreleased]:", 1)[1]
            if f"[{new_version}]:" not in links_section:
                version_links = f"[Unreleased]: https://github.com/webyneter/speech-to-console/compare/v{new_version}...HEAD\n"
                version_links += f"[{new_version}]: https://github.com/webyneter/speech-to-console/compare/v{old_version}...v{new_version}\n"
                
                new_content = re.sub(
                    r"\[Unreleased\]: .+\n",
                    version_links,
                    new_content
                )
            
            with open(changelog_path, "w") as f:
                f.write(new_content)
            
            return True
    
    print("Warning: No content found in Unreleased section of CHANGELOG.md")
    return False


def git_commands(new_version):
    """Run git commands to commit changes and create a tag"""
    commands = [
        ["git", "add", "pyproject.toml", "CHANGELOG.md"],
        ["git", "commit", "-m", f"Bump version to {new_version}"],
        ["git", "tag", "-a", f"v{new_version}", "-m", f"Release v{new_version}"],
    ]
    
    for cmd in commands:
        subprocess.run(cmd, check=True)
    
    print(f"Version bumped to {new_version} and changes committed")
    print(f"Git tag v{new_version} created")
    print("\nTo push changes and trigger a release, run:")
    print("  git push && git push origin v" + new_version)


def main():
    parser = argparse.ArgumentParser(description="Bump version and update CHANGELOG.md")
    parser.add_argument(
        "version_type", 
        choices=["patch", "minor", "major", "custom"],
        help="Type of version bump (patch, minor, major, or custom)"
    )
    parser.add_argument(
        "--version", 
        help="Custom version (only used with --type=custom)"
    )
    parser.add_argument(
        "--no-git", 
        action="store_true", 
        help="Skip git commit and tag creation"
    )
    
    args = parser.parse_args()
    
    # Get repository root
    repo_root = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True
    ).stdout.strip()
    
    pyproject_path = os.path.join(repo_root, "pyproject.toml")
    changelog_path = os.path.join(repo_root, "CHANGELOG.md")
    
    # Read current version from pyproject.toml
    current_version = read_toml(pyproject_path)["project"]["version"]
    major, minor, patch = map(int, current_version.split("."))
    
    # Calculate new version
    if args.version_type == "custom":
        if not args.version:
            parser.error("--version is required with --type=custom")
        new_version = args.version
    elif args.version_type == "patch":
        new_version = f"{major}.{minor}.{patch + 1}"
    elif args.version_type == "minor":
        new_version = f"{major}.{minor + 1}.0"
    elif args.version_type == "major":
        new_version = f"{major + 1}.0.0"
    
    print(f"Bumping version from {current_version} to {new_version}")
    
    # Update files
    old_version = update_pyproject_version(pyproject_path, new_version)
    updated = update_changelog(changelog_path, new_version, old_version)
    
    if not updated:
        print("No changes to make in CHANGELOG.md - Unreleased section is empty")
    
    # Git operations
    if not args.no_git:
        git_commands(new_version)


if __name__ == "__main__":
    main()