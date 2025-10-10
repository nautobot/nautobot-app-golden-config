#!/bin/sh

REPO_DIR="/home/git"
REPOS_SOURCE="/tmp/repos"

# Configure git globally
git config --global user.email "dev@networktocode.com"
git config --global user.name "NTC Dev"

# Create repos for each folder in /tmp/repos/
if [ -d "$REPOS_SOURCE" ]; then
    for repo_folder in "$REPOS_SOURCE"/*; do
        if [ -d "$repo_folder" ]; then
            repo_name=$(basename "$repo_folder")
            repo_path="$REPO_DIR/$repo_name"

            # Only create repo if it doesn't already exist
            if [ ! -d "$repo_path" ]; then
                mkdir -p "$REPO_DIR"
                git init "$repo_path"
                git -C "$repo_path" branch -m main
                git -C "$repo_path" config receive.denyCurrentBranch updateInstead

                # Copy contents from source folder to repo
                cp -r "$repo_folder"/* "$repo_path"/

                # Add all files and make initial commit
                git -C "$repo_path" add .
                git -C "$repo_path" commit -m "Initial commit for $repo_name"
            fi
        fi
    done
fi

# Start the git server
exec git-http-server -p 3000 /home/git