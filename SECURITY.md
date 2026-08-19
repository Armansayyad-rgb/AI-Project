# Security

RALG is designed for local and private document workflows, but this repository is not yet a hardened production system.

## Public repository rules

Do not commit:

- API keys
- access tokens
- passwords
- private customer documents
- private benchmark datasets
- acquisition or valuation strategy
- investor pitch material
- internal business plans
- model checkpoints if they are proprietary or too large

The repository already ignores common secret and private-business patterns in `.gitignore`.

## Deployment caution

Before using RALG with real company documents:

- run it in an isolated environment
- review uploaded document storage
- review logs for sensitive text
- define retention rules
- restrict network access if required
- add authentication before exposing it beyond localhost

## Responsible use

RALG should abstain when retrieved evidence is weak. It should not be used as the final authority for safety-critical, medical, legal, or financial decisions without human review.
