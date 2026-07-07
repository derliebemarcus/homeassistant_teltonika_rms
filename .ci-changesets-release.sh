#!/usr/bin/env bash
set -euo pipefail

required_variables=(
  GH_TOKEN
  CHANGESETS_REPOSITORY
  CHANGESETS_MAIN_BRANCH
  CHANGESETS_PACKAGE_FILE
  CHANGESETS_VERSION
  CHANGESETS_IMAGE
  CHANGESETS_VERSION_SYNC_COMMAND
  CHANGESETS_RELEASE_BRANCH
  CHANGESETS_AUTO_MERGE_PATCH
)
for variable in "${required_variables[@]}"; do
  if [ -z "${!variable:-}" ]; then
    echo "Missing required environment variable: ${variable}" >&2
    exit 1
  fi
done

for command_name in git gh jq podman; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "Required command is unavailable: ${command_name}" >&2
    exit 1
  }
done

test -s "$CHANGESETS_PACKAGE_FILE"
if [ -n "${CHANGESETS_ASSET:-}" ]; then
  test -s "$CHANGESETS_ASSET"
fi
test -s .changeset/config.json

repository_url="https://github.com/${CHANGESETS_REPOSITORY}.git"
gh auth setup-git
git remote set-url origin "$repository_url"
git config user.name "jenkins-release"
git config user.email "jenkins-release@users.noreply.github.com"

current_sha="$(git rev-parse HEAD)"
current_version="$(jq -er '.version' "$CHANGESETS_PACKAGE_FILE")"

run_changesets_version() {
  podman run --rm \
    --pull=always \
    --userns=keep-id \
    --volume "$PWD:/workspace:z" \
    --workdir /workspace \
    --env CHANGESETS_VERSION \
    --env CHANGESETS_VERSION_SYNC_COMMAND \
    "$CHANGESETS_IMAGE" \
    bash -lc '
      set -euo pipefail
      npx --yes "@changesets/cli@${CHANGESETS_VERSION}" version
      bash -lc "$CHANGESETS_VERSION_SYNC_COMMAND"
    '
}

release_notes_file() {
  local version="$1"
  local output="$2"

  : > "$output"
  if [ -s CHANGELOG.md ]; then
    awk -v version="$version" '
      $0 == "## " version { found = 1; next }
      found && /^## / { exit }
      found { print }
    ' CHANGELOG.md > "$output"
  fi

  if [ ! -s "$output" ]; then
    printf 'Release %s\n' "$version" > "$output"
  fi
}

publish_current_version() {
  local tag="v${current_version}"
  local tag_sha=""
  local release_is_draft=""
  local asset_name=""
  local asset_present="false"

  if git ls-remote --exit-code --tags origin "refs/tags/${tag}" >/dev/null 2>&1; then
    git fetch --force origin "refs/tags/${tag}:refs/tags/${tag}"
    tag_sha="$(git rev-list -n 1 "$tag")"
    if [ "$tag_sha" != "$current_sha" ]; then
      echo "Tag ${tag} belongs to ${tag_sha}; current main commit is ${current_sha}."
      echo "No release publication is required for this build."
      return
    fi
  else
    git tag -a "$tag" -m "$tag" "$current_sha"
    git push origin "refs/tags/${tag}"
  fi

  if ! gh release view "$tag" --repo "$CHANGESETS_REPOSITORY" >/dev/null 2>&1; then
    notes_file="$(mktemp)"
    release_notes_file "$current_version" "$notes_file"
    gh release create "$tag" \
      --repo "$CHANGESETS_REPOSITORY" \
      --verify-tag \
      --title "$tag" \
      --notes-file "$notes_file" \
      --draft
    rm -f "$notes_file"
  fi

  release_is_draft="$(
    gh release view "$tag" \
      --repo "$CHANGESETS_REPOSITORY" \
      --json isDraft \
      --jq '.isDraft'
  )"

  if [ -n "${CHANGESETS_ASSET:-}" ]; then
    asset_name="$(basename "$CHANGESETS_ASSET")"
    asset_present="$(
      gh release view "$tag" \
        --repo "$CHANGESETS_REPOSITORY" \
        --json assets |
        jq -r --arg name "$asset_name" '[.assets[].name == $name] | any'
    )"
  fi

  if [ "$release_is_draft" = "true" ]; then
    if [ -n "${CHANGESETS_ASSET:-}" ]; then
      gh release upload "$tag" \
        "$CHANGESETS_ASSET" \
        --repo "$CHANGESETS_REPOSITORY" \
        --clobber
    fi
    gh release edit "$tag" \
      --repo "$CHANGESETS_REPOSITORY" \
      --draft=false
    gh release view "$tag" \
      --repo "$CHANGESETS_REPOSITORY" \
      --json tagName,url,isDraft,assets
    return
  fi

  if [ -z "${CHANGESETS_ASSET:-}" ]; then
    echo "Release ${tag} is already published; no release asset is configured."
    return
  fi

  if [ "$asset_present" = "true" ]; then
    echo "Release ${tag} is already published with ${asset_name}."
    return
  fi

  echo "Release ${tag} is immutable and missing ${asset_name}." >&2
  exit 1
}

create_or_update_version_pr() {
  local old_version="$current_version"
  local release_branch="$CHANGESETS_RELEASE_BRANCH"

  git fetch origin \
    "refs/heads/${CHANGESETS_MAIN_BRANCH}:refs/remotes/origin/${CHANGESETS_MAIN_BRANCH}"
  git fetch origin \
    "refs/heads/${release_branch}:refs/remotes/origin/${release_branch}" \
    >/dev/null 2>&1 || true
  git checkout -B "$release_branch" "origin/${CHANGESETS_MAIN_BRANCH}"

  run_changesets_version

  new_version="$(jq -er '.version' "$CHANGESETS_PACKAGE_FILE")"
  if [ "$new_version" = "$old_version" ]; then
    echo 'Changesets did not change the package version.' >&2
    exit 1
  fi

  git add -A
  if git diff --cached --quiet; then
    echo 'Changesets produced no version changes.' >&2
    exit 1
  fi

  git commit -m "change: prepare release ${new_version}"
  git push --force-with-lease origin "HEAD:refs/heads/${release_branch}"

  pr_url="$(
    gh pr list \
      --repo "$CHANGESETS_REPOSITORY" \
      --base "$CHANGESETS_MAIN_BRANCH" \
      --head "$release_branch" \
      --state open \
      --limit 1 \
      --json url \
      --jq '.[0].url // empty'
  )"

  pr_title="change: release ${new_version}"
  pr_body="$(cat <<EOF
## Summary

- consume pending Changesets
- update the package version to \`${new_version}\`
- update the changelog and repository-specific version sources

After this PR is merged and the Jenkins main build passes, Jenkins creates tag \`v${new_version}\`, creates a draft GitHub Release, uploads any configured release asset and publishes the immutable release only after its contents are complete.
EOF
)"

  if [ -z "$pr_url" ]; then
    pr_url="$(
      gh pr create \
        --repo "$CHANGESETS_REPOSITORY" \
        --base "$CHANGESETS_MAIN_BRANCH" \
        --head "$release_branch" \
        --title "$pr_title" \
        --body "$pr_body"
    )"
  else
    gh pr edit "$pr_url" \
      --repo "$CHANGESETS_REPOSITORY" \
      --title "$pr_title" \
      --body "$pr_body"
  fi

  IFS=. read -r old_major old_minor old_patch <<< "$old_version"
  IFS=. read -r new_major new_minor new_patch <<< "$new_version"
  if [ "$CHANGESETS_AUTO_MERGE_PATCH" = "true" ] && \
     [ "$old_major" = "$new_major" ] && \
     [ "$old_minor" = "$new_minor" ] && \
     [ "$new_patch" -gt "$old_patch" ]; then
    if ! gh pr merge --auto --squash "$pr_url" --repo "$CHANGESETS_REPOSITORY"; then
      echo 'Native auto-merge could not be enabled; the patch release PR remains open.' >&2
    fi
  fi
}

pending_changesets="$(
  find .changeset -maxdepth 1 -type f -name '*.md' ! -name 'README.md' -print
)"

if [ -n "$pending_changesets" ]; then
  echo 'Pending Changesets:'
  printf '%s\n' "$pending_changesets"
  create_or_update_version_pr
else
  publish_current_version
fi
