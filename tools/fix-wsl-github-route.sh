#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: fix-wsl-github-route.sh <github-ip>" >&2
    exit 2
fi

github_ip="$1"
marker="# CS50P auto-selected GitHub route"
temporary_hosts="$(mktemp)"
trap 'rm -f "$temporary_hosts"' EXIT

awk -v marker="$marker" 'index($0, marker) == 0' /etc/hosts > "$temporary_hosts"
printf '%s\tgithub.com\t%s\n' "$github_ip" "$marker" >> "$temporary_hosts"
install -m 0644 "$temporary_hosts" /etc/hosts
