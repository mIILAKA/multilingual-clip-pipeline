# Security policy

This repository intentionally excludes production media, transcripts, analytics, publishing state,
cookies, OAuth files, API keys, model caches, and generated output.

Credentials must be supplied through environment variables or files outside the repository. The
`.gitignore` contains defensive patterns for common local credential files, but contributors should
still run a secret scanner before publishing history.

The synthetic `demo` command confines generated files to `media/` and `output/` under its selected
root. It rejects path traversal and absolute paths outside those directories, limits generated media
to five minutes, applies subprocess timeouts, and does not overwrite existing files unless `--force`
is explicitly supplied. These controls protect the demonstration path; this repository is not a
sandbox for processing untrusted FFmpeg inputs.

If a credential is committed, revoke it first. Removing it from Git history does not make the leaked
credential safe again.
