# Sanitized validation

Physical validation: one Victus 16-r0035nt / 8BBE / 7P6L3EA#AB8 / F.31. The device owner confirmed Fn-off → menu-on, zero → fully off, and reopening. They also confirmed operation after reboot and that slider lag was resolved.

Running kernel: 7.2.9-1-cachyos. DKMS builds and installations passed for that kernel and 6.18.55-1-cachyos-lts. LTS boot was not tested. The loaded module matched the installed DKMS build. Colors, presets and brightness survived user-service restart. Menu API off/on cycles passed.

Fake-EC testing covered combined gate state, unrelated bit/index preservation, partial state reporting, firmware identity scope and transaction rollback after injected write failures. These are simulated checks, not evidence of support for a second laptop.

QML checks covered fast slider requests, stale brightness notifications, duplicate requests, error recovery, bounds, opening the preset editor, invalid values, defaults/cancel and saving unchanged current presets. Python checks covered color channel ordering, validation, persistence, device recreation and delayed UPower readiness. Sleep and screen events were simulated in this final test cycle; no new physical sleep/unplug test was performed.

The sanitized public bundle's fake-device Python checks, fake-EC harness and slider QML checks also passed. Applying the review diff to its pinned baseline reproduced the tested driver source byte-for-byte. Raw logs, screen layouts, screenshots, exact session times, owner-chosen presets and machine identifiers are not attached.
