// SPDX-License-Identifier: GPL-2.0-or-later
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
typedef uint8_t u8;typedef int acpi_status;
#define BIT(x) (1U<<(x))
#define EIO 5
#define EBUSY 16
#define ACPI_FAILURE(x) ((x)!=0)
#define DEFINE_MUTEX(x) int x
#define DMI_BOARD_NAME 0
#define DMI_PRODUCT_SKU 1
#define DMI_BIOS_VERSION 2
static const char *dmi[]={"8BBE","7P6L3EA#AB8","F.31"};
static u8 regs[256],indexed[65536];static int writes,fail_at;static bool locked;
static bool dmi_match(int key,const char *value){return !strcmp(dmi[key],value);}
static void mutex_lock(int *m){}static void mutex_unlock(int *m){}
static acpi_status acpi_acquire_mutex(void *a,const char *b,int c){assert(!locked);locked=true;return 0;}
static void acpi_release_mutex(void *a,const char *b){assert(locked);locked=false;}
static int ec_read(int addr,u8 *value){assert(locked);*value=addr==0x5f?indexed[regs[0x5d]+256*regs[0x5e]]:regs[addr];return 0;}
static int ec_write(int addr,u8 value){assert(locked);if(++writes==fail_at)return -EIO;if(addr==0x5f)indexed[regs[0x5d]+256*regs[0x5e]]=value;else regs[addr]=value;return 0;}
/* Victus 16-r0035nt, board 8BBE, BIOS F.31. Fn-only snapshots and a
 * physical-light test verified that all three controls are required:
 * EC A1 bit 0, EC 07 four two-bit zone levels, indexed 1832 bit 4.
 * The BIOS setters acknowledge writes without applying the full state.
 * Use the EC transport; preserve every unrelated bit and the index selector.
 * Restrict this empirical quirk to the exact hardware/firmware tested. */
#define VICTUS_KBD_INDEX_LOW 0x5d
#define VICTUS_KBD_INDEX_HIGH 0x5e
#define VICTUS_KBD_INDEX_DATA 0x5f
#define VICTUS_KBD_OUTPUT_INDEX 0x1832
#define VICTUS_KBD_OUTPUT_MASK BIT(4)
#define VICTUS_KBD_MASTER 0xa1
#define VICTUS_KBD_MASTER_MASK BIT(0)
#define VICTUS_KBD_ZONE_LEVELS 0x07
#define VICTUS_KBD_ZONE_ON 0xaa
#define VICTUS_KBD_INDEX_MUTEX "\\_SB.PC00.LPCB.EC0.FAMX"
static DEFINE_MUTEX(victus_kbd_gate_lock);

static bool hp_victus_kbd_ec_supported(void)
{
	return dmi_match(DMI_BOARD_NAME, "8BBE") &&
	       dmi_match(DMI_PRODUCT_SKU, "7P6L3EA#AB8") &&
	       dmi_match(DMI_BIOS_VERSION, "F.31");
}

/* enabled=-1 reads the complete gate; 0/1 apply an off/on transaction.
 * The firmware's FAMX mutex also protects its EIDR/EIDW index accesses. */
static int hp_victus_kbd_ec_gate(int enabled)
{
	acpi_status status;
	u8 index_low, index_high, master, zones, output;
	u8 new_master, new_zones, new_output, read_master, read_zones, read_output;
	int ret = -EIO, restore_ret;
	bool changed = false;

	mutex_lock(&victus_kbd_gate_lock);
	status = acpi_acquire_mutex(NULL, VICTUS_KBD_INDEX_MUTEX, 1000);
	if (ACPI_FAILURE(status)) {
		ret = -EBUSY;
		goto unlock;
	}
	if (ec_read(VICTUS_KBD_INDEX_LOW, &index_low) ||
	    ec_read(VICTUS_KBD_INDEX_HIGH, &index_high))
		goto release;
	if (ec_write(VICTUS_KBD_INDEX_LOW, VICTUS_KBD_OUTPUT_INDEX & 0xff) ||
	    ec_write(VICTUS_KBD_INDEX_HIGH, VICTUS_KBD_OUTPUT_INDEX >> 8) ||
	    ec_read(VICTUS_KBD_INDEX_DATA, &output) ||
	    ec_read(VICTUS_KBD_MASTER, &master) ||
	    ec_read(VICTUS_KBD_ZONE_LEVELS, &zones))
		goto restore_index;

	if (enabled < 0) {
		ret = !!((master & VICTUS_KBD_MASTER_MASK) &&
			 (zones & 0x03) && (output & VICTUS_KBD_OUTPUT_MASK));
		goto restore_index;
	}
	new_master = enabled ? master | VICTUS_KBD_MASTER_MASK :
			      master & ~VICTUS_KBD_MASTER_MASK;
	new_zones = enabled ? VICTUS_KBD_ZONE_ON : 0;
	new_output = enabled ? output | VICTUS_KBD_OUTPUT_MASK :
			      output & ~VICTUS_KBD_OUTPUT_MASK;
	changed = true;
	if (enabled) {
		if (ec_write(VICTUS_KBD_MASTER, new_master) ||
		    ec_write(VICTUS_KBD_ZONE_LEVELS, new_zones) ||
		    ec_write(VICTUS_KBD_INDEX_DATA, new_output))
			goto rollback;
	} else {
		if (ec_write(VICTUS_KBD_INDEX_DATA, new_output) ||
		    ec_write(VICTUS_KBD_ZONE_LEVELS, new_zones) ||
		    ec_write(VICTUS_KBD_MASTER, new_master))
			goto rollback;
	}
	if (ec_read(VICTUS_KBD_MASTER, &read_master) ||
	    ec_read(VICTUS_KBD_ZONE_LEVELS, &read_zones) ||
	    ec_read(VICTUS_KBD_INDEX_DATA, &read_output) ||
	    (read_master & VICTUS_KBD_MASTER_MASK) !=
		(new_master & VICTUS_KBD_MASTER_MASK) ||
	    read_zones != new_zones ||
	    (read_output & VICTUS_KBD_OUTPUT_MASK) !=
		(new_output & VICTUS_KBD_OUTPUT_MASK))
		goto rollback;
	ret = 0;
	goto restore_index;
rollback:
	/* Restore only the fields this transaction owns, keeping unrelated
	 * master/output bits even if firmware updated them during the write. */
	if (changed) {
		if (!ec_read(VICTUS_KBD_INDEX_DATA, &read_output))
			ec_write(VICTUS_KBD_INDEX_DATA,
				 (read_output & ~VICTUS_KBD_OUTPUT_MASK) |
				 (output & VICTUS_KBD_OUTPUT_MASK));
		ec_write(VICTUS_KBD_ZONE_LEVELS, zones);
		if (!ec_read(VICTUS_KBD_MASTER, &read_master))
			ec_write(VICTUS_KBD_MASTER,
				 (read_master & ~VICTUS_KBD_MASTER_MASK) |
				 (master & VICTUS_KBD_MASTER_MASK));
	}
restore_index:
	restore_ret = ec_write(VICTUS_KBD_INDEX_LOW, index_low);
	if (ec_write(VICTUS_KBD_INDEX_HIGH, index_high) || restore_ret)
		ret = -EIO;
release:
	acpi_release_mutex(NULL, VICTUS_KBD_INDEX_MUTEX);
unlock:
	mutex_unlock(&victus_kbd_gate_lock);
	return ret;
}

static void reset(void){memset(regs,0,sizeof(regs));memset(indexed,0,sizeof(indexed));regs[0xa1]=0xa0;regs[0x5d]=0x56;regs[0x5e]=0x34;indexed[0x1832]=0xaf;writes=0;fail_at=0;}
static void selector(void){assert(regs[0x5d]==0x56&&regs[0x5e]==0x34&&!locked);}
int main(void){
 reset();assert(hp_victus_kbd_ec_supported());dmi[2]="F.32";assert(!hp_victus_kbd_ec_supported());dmi[2]="F.31";
 assert(hp_victus_kbd_ec_gate(-1)==0);selector();
 assert(hp_victus_kbd_ec_gate(1)==0);selector();assert(regs[0xa1]==0xa1&&regs[7]==0xaa&&indexed[0x1832]==0xbf);
 assert(hp_victus_kbd_ec_gate(-1)==1);selector();
 indexed[0x1832]&=~0x10;assert(hp_victus_kbd_ec_gate(-1)==0);selector();
 assert(hp_victus_kbd_ec_gate(1)==0);assert(hp_victus_kbd_ec_gate(0)==0);selector();assert(regs[0xa1]==0xa0&&regs[7]==0&&indexed[0x1832]==0xaf);
 for(int failure=1;failure<=5;failure++){reset();fail_at=failure;assert(hp_victus_kbd_ec_gate(1)<0);selector();assert(regs[0xa1]==0xa0&&regs[7]==0&&indexed[0x1832]==0xaf);}
 puts("PASS: complete gate, preserved bits/selector, partial state, BIOS scope, failed transaction rollback");
}
