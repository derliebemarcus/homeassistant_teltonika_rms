# Troubleshooting

## Validation fails

Run the documented local test commands and inspect the first failing quality gate.

## Runtime cannot reach an external dependency

Verify DNS, network reachability, credentials, permissions, quotas, and upstream status.

## Configuration is rejected

Compare the deployed values with the configuration reference and remove stale generated artifacts or caches where applicable.

## A release or deployment is unhealthy

Stop further automation and follow the rollback procedure.
