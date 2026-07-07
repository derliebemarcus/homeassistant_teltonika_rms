# Troubleshooting

## Validation fails

Run the documented local test commands and inspect the first failing quality gate.

## Runtime cannot reach an external dependency

Verify DNS, network reachability, credentials, permissions, quotas, and upstream status.

## Configuration is rejected

Compare the deployed values with the configuration reference and remove stale generated artifacts or caches where applicable.

## A release or deployment is unhealthy

Stop further automation and follow the rollback procedure.

## Shared CI image failures

Confirm Harbor can pull `homeassistant-integration-ci:3.14`, then inspect dependency
installation and the bootstrap stash. Dependency failures belong to `requirements.txt`;
missing native or shared tools require a maintenance image update.
