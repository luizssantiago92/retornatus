# Security policy

## Supported versions

Security fixes land on `main` and ship in the next release. Older versions published to PyPI are not patched as separate lines.

## Reporting a vulnerability

Report security vulnerabilities privately through [GitHub Security Advisories](https://github.com/luizssantiago92/retornatus/security/advisories/new).

Do not open a public issue for a suspected vulnerability.

Include the affected version, the impact, and a minimal way to reproduce the problem when you have one. A maintainer will acknowledge the report. Please give the project time to ship a fix before any public disclosure.

## Local secrets and signing keys

`retornatus init` appends a delimited block to `.gitignore` when `# retornatus-gitignore:begin` is missing. The block ignores the local index and cache (`.retornatus/index/`, `.retornatus/runtime/`), `*.pem`, `*.key`, `.env`, and `.env.*`. It leaves `!.env.example` and `!.retornatus/keys/*.pub` committable. A second run does not duplicate the block or remove existing lines.

`receipt keygen` writes the Ed25519 private key outside the repository (the user config directory) or, with `--print`, only to stdout for a CI secret. It does not write that key inside the project. If git already tracks a `*.pem` or `*.key` file, `init` and `receipt keygen` print a warning. Remove that file from the index. Do not commit private keys.
