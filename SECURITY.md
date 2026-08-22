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
- proprietary model checkpoints

The repository ignores common secret and private-business patterns through `.gitignore`, but secret scanning and human review are still required before publishing changes.

## Current security boundary

The public FastAPI and Gradio components should be treated as **local-development interfaces** unless additional controls are added.

Before exposing RALG beyond localhost, add and verify:

- authentication and authorization
- TLS termination
- request-size limits
- rate limiting
- upload quotas
- tenant/user isolation where applicable
- structured error handling that does not expose internal exception details
- audit logging appropriate to the deployment

## Document-upload risks

Uploaded PDF, DOCX, and TXT files are untrusted input.

Deployments handling real documents should:

- enforce extension and size limits
- store uploads outside executable/source directories
- sanitize generated filenames and paths
- avoid executing embedded content or macros
- define document and log retention rules
- restrict filesystem permissions
- isolate parsing/indexing from sensitive host resources where practical

## Private-data handling

Before using RALG with company documents:

- review where uploaded text, indexes, logs, exports, and feedback are persisted
- determine whether retrieved source text can appear in logs or error messages
- restrict network access when offline/local-only operation is required
- define deletion and backup procedures
- verify that no external model/provider is enabled unintentionally

## Dependency and build security

For reproducible or sensitive deployments:

- review dependency updates before upgrading
- pin or lock production dependencies more tightly than development ranges when appropriate
- build images from reviewed commits
- scan container images and Python dependencies for known vulnerabilities
- do not place credentials in Dockerfiles, compose files, committed `.env` files, or command history

## Model and retrieval safety

RALG should abstain when evidence is weak. Retrieval confidence is not equivalent to factual certainty, and retrieved text may itself be incorrect or malicious.

For safety-critical workflows:

- show source evidence to the operator
- require human review before acting on high-impact answers
- test false-support and false-premise behavior on domain-specific documents
- keep benchmark/evaluation data separate from production tuning where possible

RALG should not be used as the final authority for safety-critical, medical, legal, or financial decisions without appropriate human review.

## Reporting a vulnerability

Do not publish credentials, private documents, or exploit details in a public issue. Contact the repository owner privately through an appropriate GitHub contact channel when confidential disclosure is necessary.
