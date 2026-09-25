# Incident Response Runbook

## Severity Levels
Incidents are classified as SEV1 (full outage), SEV2 (major feature degraded), or SEV3 (minor, cosmetic, or single-customer issue). SEV1 incidents require paging the on-call engineer within 5 minutes of detection.

## Incident Commander Role
Every SEV1 and SEV2 incident must have a designated Incident Commander (IC) within 10 minutes of declaration. The IC is not permitted to also be the engineer actively debugging the issue.

## Communication Cadence
During a SEV1 incident, status updates must be posted to the #incidents channel every 15 minutes until the incident is resolved or downgraded. SEV2 incidents require updates every 30 minutes.

## Postmortem Requirement
A written postmortem is required for all SEV1 incidents within 5 business days of resolution. SEV2 postmortems are optional but encouraged. SEV3 incidents never require a postmortem.

## Rollback Authority
Any on-call engineer has standing authority to roll back a deployment during a SEV1 or SEV2 incident without needing manager approval first.
