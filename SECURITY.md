# Security policy

This repository intentionally excludes production media, transcripts, analytics, publishing state,
cookies, OAuth files, API keys, model caches, and generated output.

Credentials must be supplied through environment variables or files outside the repository. The
`.gitignore` contains defensive patterns for common local credential files, but contributors should
still run a secret scanner before publishing history.

If a credential is committed, revoke it first. Removing it from Git history does not make the leaked
credential safe again.
