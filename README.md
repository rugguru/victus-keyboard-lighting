# Victus keyboard lighting — review bundle

This source bundle documents and preserves a working, device-specific keyboard lighting fix and an optional Plasma 6 control applet. It is a maintainer-review draft, not a universal installer or a distribution-endorsed release.

## Tested scope

One HP Victus 16-r0035nt, board 8BBE, SKU 7P6L3EA#AB8, BIOS F.31. These are non-unique product/firmware identifiers required to restrict the hardware quirk. They are not a serial number or device UUID. The RGB user service targets the single-zone LED `hp::kbd_backlight`; four-zone layouts are not supported by this user interface.

The EC fix activates only for that exact board/SKU/BIOS match. Do not remove the identity guard to claim support for other Victus models. Other firmware or hardware requires independent evidence and review.

## Contents

- `driver/`: the tested, TUXOV-derived hp-wmi source and DKMS/build metadata. This replaces hp-wmi and inherits fan/profile functionality from that project. It is not a standalone keyboard-only module.
- `patches/`: unsigned review diff against the public commit recorded in PROVENANCE.json. This applies to the TUXOV tree, not directly to Linux mainline.
- `service/`: per-user brightness/color bridge; default presets only, no owner's saved colors.
- `applet/`: optional Plasma 6 brightness/color applet with slider request coalescing and editable RGB presets. It currently contains Turkish UI text and depends on Plasma's private brightness plugin; release packaging and translation need review.
- `tests/`: non-hardware unit checks and a fake-EC transaction harness. They do not install modules or alter a running keyboard.
- `docs/`: sanitized test findings, publication plan, privacy explanation and an upstream issue draft.

Personal installation scripts are deliberately excluded. This bundle does not modify a user's theme, panels, splash, monitor layout or existing services. No installation is performed by opening the archive.

## Remaining release work

A maintainer should review the direct EC access, firmware mutex, rollback/error behavior, LED interactions and the broader WMI fallback changes. Separate changes into logical commits before proposing them upstream. Recheck any firmware paths outside the exact EC guard.

For a distributable installer, implement per-user service registration with runtime discovery of username, home directory and UID, a restricted color-write permission mechanism, distro dependencies, upgrade/removal/rollback behavior, Secure Boot module handling where applicable, multi-device support and translations. The machine-specific installer is not included and should not be reused as a public installer.

Compile only against matching kernel headers. `bash driver/build-module.sh /path/to/kernel/build "$PWD/driver"` builds for technical review; do not load the resulting module on unverified hardware. No binary module is shipped. Build success does not establish hardware compatibility.

## Licensing and provenance

Original SPDX notices, copyright headers and public upstream-author attribution are preserved. Driver and new bridge/control sources are GPL-2.0-or-later; existing KDE files retain their declared GPL/LGPL licenses. LGPL-2.0-or-later components may use the bundled LGPL 2.1 text under their or-later option. See LICENSES and NOTICE.md.

The local changes were prepared with AI assistance and physically verified by a device owner. No maintainer review, endorsement or third-party test result is claimed. No author identity or Signed-off-by has been fabricated. The unsigned diff is a review artifact, not a ready-to-send kernel submission.
