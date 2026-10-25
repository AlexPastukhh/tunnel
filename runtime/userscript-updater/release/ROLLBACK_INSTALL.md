# Side-by-side installation rollback

1. Close Project Checker and wait for all CLI/transaction workers to finish.
2. If an operation is pending, open the same protected version and inspect its
   recovery preview first. Restore/rollback only the shown scope; preserve state,
   original backups, conflict backups and reports. Never recursively replace an
   approved target from an installation archive.
3. Start the previous independently accepted version from its explicit launcher.
   Keep its original data/profile/receipt. A new version's registry and shared
   policies are not silently migrated into the old version.
4. Keep the failed candidate directory for review. Removing its program files,
   optional Python installer registration, markers and fixture data is an owner
   action after recovery. No automatic uninstaller touches external targets,
   Loader, another Python installation or the previous version.

The staging installer refuses an existing installation/data root, so it cannot
overwrite a working version. The normal runtime never repairs itself or syncs
code/dependencies from Repo. Changed code/closure requires a newly reviewed
version and native acceptance; editing a manifest to hide drift is not rollback.
