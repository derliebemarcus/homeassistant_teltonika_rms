# Deployment

1. Jenkins builds the dedicated Teltonika RMS CI image and runs all quality gates.
2. Changesets maintains version synchronization and release intent.
3. A tagged release packages the integration for HACS installation.

Documentation-only changes must never execute deployment or publication stages.
