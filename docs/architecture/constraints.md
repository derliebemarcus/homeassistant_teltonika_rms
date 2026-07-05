# Architectural constraints

- The integration must respect RMS request quotas.
- OAuth2 and PAT authentication must remain supported.
- Optional device capabilities and endpoint availability vary by model and scope.
- Home Assistant async I/O requirements prohibit blocking runtime operations.
