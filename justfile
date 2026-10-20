set shell := ["zsh", "-eu", "-o", "pipefail", "-c"]

repo_root := justfile_directory()

default:
    @just --list

# Link every top-level portable skill into both supported user-level skill roots.
sync:
    #!/usr/bin/env zsh
    set -euo pipefail

    source_root="{{repo_root}}"
    target_roots=("$HOME/.agents/skills" "$HOME/.claude/skills")

    mkdir -p "${target_roots[@]}"

    for skill_file in "$source_root"/*/SKILL.md(N); do
      skill_dir="${skill_file:h}"
      skill_name="${skill_dir:t}"

      for target_root in "${target_roots[@]}"; do
        destination="$target_root/$skill_name"

        if [[ -L "$destination" ]]; then
          if [[ "$destination:A" == "$skill_dir:A" ]]; then
            print -r -- "unchanged $destination"
            continue
          fi
          rm "$destination"
        elif [[ -e "$destination" ]]; then
          print -u2 -r -- "refusing to replace unmanaged path: $destination"
          exit 1
        fi

        ln -s "$skill_dir" "$destination"
        print -r -- "linked $destination -> $skill_dir"
      done
    done
