#!/bin/sh
set -eu

repo_path="${CI_PRIMARY_REPOSITORY_PATH:?CI_PRIMARY_REPOSITORY_PATH is required}"
cd "$repo_path"

if ! command -v xcodegen >/dev/null 2>&1; then
  if ! command -v brew >/dev/null 2>&1; then
    printf 'XcodeGen and Homebrew are unavailable in this Xcode Cloud environment.\n' >&2
    exit 1
  fi
  brew install xcodegen
fi

xcodegen generate --spec iosApp/project.yml
