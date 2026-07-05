# Security model

Teltonika RMS Home Assistant Integration uses least-privilege credentials and keeps secrets outside Git. External inputs, webhook payloads, API responses, files, and user data are validated at trust boundaries. CI performs dependency, source, secret, and configuration checks. Operational logs and support reports must remove sensitive values.
