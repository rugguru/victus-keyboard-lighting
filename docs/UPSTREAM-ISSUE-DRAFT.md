# hp-wmi: single-zone Victus keyboard cannot reopen after Fn-off

On one Victus 16-r0035nt (board 8BBE, SKU 7P6L3EA#AB8, BIOS F.31), positive keyboard brightness requests were accepted while the physical keyboard stayed off after Fn+F4. Zeroing RGB could darken the keyboard but did not solve reopening after the physical hotkey closed the gate.

A locally tested change applies the three Fn-controlled fields together: standard EC A1 bit 0, EC 07 zone levels, and indexed EC 1832 bit 4. Index access uses the firmware FAMX mutex and restores the selector. Unrelated bits are preserved; failed writes are rolled back. The empirical EC path is guarded by the exact board/SKU/BIOS tuple.

The attached unsigned diff is against the public TUXOV baseline pinned in PROVENANCE.json. It includes related zero-RGB fallback, brightness restoration/reporting and build compatibility changes; these should be split/reviewed before merging. It is not a mainline patch.

The device owner physically confirmed reopening after Fn-off, full off at zero, reopening again and persistence after reboot. Current and LTS kernel builds passed; only the current kernel was boot-tested. The accompanying source/tests provide transaction and userspace validation. No raw machine dumps or personal logs are attached. Please review the EC access and LED semantics; no additional model support is claimed.

AI assistance was used in preparing this change. No maintainer approval or sign-off is implied. What would be the preferred way to structure this device quirk and the related LED changes for review?
