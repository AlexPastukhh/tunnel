# Candidate Project Checker (source only)

Implementation workspace for a full Windows project checker and controlled external promotion according to Candidate Pre-work Composition v4 (A4).

NOT a trusted installation or authorization to run project code on Windows.

## Partial E-01 foundation
- Serializable project registration: check-only or target mappings; file, directory, mixed selections; policy pack identifiers.
- Source inventory with SHA-256 and review bytes snapshot, rescan detection of source additions/deletions/modifications.
- Synthetic Python unit tests for source scope, collisions, Unicode, symlinks, mappings, and invalidated snapshots.

INCOMPLETE: Windows no-follow/race-free secure file handles, scanner adapters and trustworthy coverage, policy pack lifecycle, preview and approval, target checks, backups/recovery, GUI, deployment and OS trust-boundary verification. Path prechecks are not secure against TOCTOU. No file promotion API exists.

Test within Fortis Repo: python3 -m unittest discover -s tests -v

Do not execute, install or consume this Repo source as the trusted Windows application.
