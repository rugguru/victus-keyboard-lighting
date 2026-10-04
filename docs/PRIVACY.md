# Privacy scope

The archive was built from an explicit source-file selection rather than a workstation backup. It includes code, documentation, licenses, non-hardware tests and a review diff.

Excluded: owner's account name/home path, local UID/GID, hostname, machine/boot IDs, serial numbers, DMI dumps, ACPI/BIOS dumps, MAC/IP addresses, monitor EDIDs/layouts, personal presets/brightness files, screenshots, raw service/kernel logs, recovery archives, chat records, Git history/configuration, compiled modules, object files and Python caches.

Kept intentionally: product model, board identifier, product SKU, BIOS version, tested kernel versions and public upstream-author attribution. Product identifiers are non-unique compatibility data required by the guard. They may still identify the tested hardware class.

ZIP member paths are relative. Member timestamps are fixed, permissions are normalized, and ZIP extra/comment fields are empty; no local owner username, UID/GID or filesystem extended attributes are exported. Checksums contain relative names only.

PRIVACY-AUDIT.json records the scans and exclusions. Pattern scanning is a bounded check, not a guarantee about every possible inference. Recheck any newly added files before publication. Sharing this archive does not anonymize a publishing account, commit author, email headers or future support messages. Use only a deliberate public identity and contact address.

No telemetry, background upload or publishing code is included. The service writes settings locally; the included source does not ship any saved owner preference.
