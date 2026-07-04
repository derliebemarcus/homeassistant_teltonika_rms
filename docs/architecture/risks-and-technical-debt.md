# Risks and technical debt

- RMS endpoint behavior and OpenAPI definitions can change.
- OAuth scope changes may require reauthentication.
- Socket.IO availability can vary and requires a polling fallback.
- Device support beyond validated models can expose untested capability combinations.

Risks are reviewed during upgrades, incidents, and architecture decisions.
