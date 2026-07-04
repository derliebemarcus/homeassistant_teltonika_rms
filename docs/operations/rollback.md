# Rollback

1. Stop release or deployment automation.
2. Identify the last known-good immutable version or configuration backup.
3. Restore the artifact, data, configuration, and secrets required by that version.
4. Run health, compatibility, and smoke verification.
5. Correct the defect in a new change; never rewrite an existing release tag.
