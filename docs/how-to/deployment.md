# Deployment

1. Jenkins pulls the shared Home Assistant integration CI image and runs all quality gates.
2. Changesets maintains version synchronization and release intent.
3. A tagged release packages the integration for HACS installation.

Documentation-only changes must never execute deployment or publication stages.

## CI runtime publication

The shared Home Assistant integration CI image is built and published by the
`maintenance` repository. This repository consumes the stable `3.14` tag and does not
build or publish a project-specific image.
