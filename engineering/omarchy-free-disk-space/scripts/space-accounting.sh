#!/bin/bash

# Read available filesystem bytes; unavailable data remains explicitly unknown.
disk_available_bytes() {
  local output available
  if output=$(df -B1 --output=avail -- "$1" 2>/dev/null); then
    available=$(awk 'NR==2 {print $1}' <<<"$output")
    if [[ $available =~ ^[0-9]+$ ]]; then
      printf '%s' "$available"
      return
    fi
  fi
  printf 'unknown'
}

# A rename to Trash is not reclamation; other actions need measured verification.
disk_physical_recovery() {
  if [[ $1 == "trash-path" ]]; then
    printf '0'
  else
    printf 'unknown'
  fi
}
