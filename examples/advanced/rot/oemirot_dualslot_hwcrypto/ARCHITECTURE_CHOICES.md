# Bootloader architecture — the choices, explained from zero

Companion to [`DOC.md`](DOC.md). `DOC.md` describes **the example as it is**;
[`UPDATE_FLOWS.md`](UPDATE_FLOWS.md) draws the update sequence for each architecture.
This file answers: *what else could it be?* — every knob we can turn, what each one means in plain
language, which combinations are legal, and a short list of realistic complete
configurations to choose between.

No prior bootloader knowledge assumed. Start at §0.

---

## 0. Sixty-second primer

A microcontroller has one flash memory and runs whatever code sits at the boot address.
If an attacker (or a corrupted download) can change that code, they own the product
forever. A **secure boot** solves this by splitting the flash in two parts:

- A small **bootloader** that can never be changed after manufacturing — the
  **Root of Trust (RoT)**. It is the first thing that runs.
- The **application** — the actual product firmware, which *can* be updated.

On every power-up the RoT checks the application with cryptography *before* letting it
run. If the check fails, the application never executes.

The vocabulary you need:

| Term | Plain meaning |
|---|---|
| **Image** | A firmware binary plus a header and a metadata trailer (version, signature, hashes). Not just raw code. |
| **Slot** | A reserved region of flash sized to hold one image. |
| **Primary slot** | Where the firmware that actually runs lives. |
| **Secondary slot** | Where a newly downloaded firmware waits to be checked and installed. |
| **Signing** | The manufacturer computes a cryptographic proof, with a **private key** that never leaves the factory, that this exact image is genuine. |
| **Verifying** | The RoT checks that proof with the matching **public key**, which *is* on the device. Public key leaking is harmless; private key leaking is fatal. |
| **Encryption** | Separate from signing. Scrambles the image so nobody can *read* your firmware. Signing stops forgery; encryption stops copying. |
| **Rollback (revert)** | Going back to the previous firmware because the new one is broken. |
| **Anti-rollback** | *Preventing* a return to an old firmware that has a known security hole. Confusingly, the opposite goal — see §2.3. |
| **RDP** (Readout Protection) | An option-byte setting that blocks the debugger from reading flash. Protects against someone plugging in a probe and dumping your firmware and keys. |
| **WRP** (Write Protection) | Option bytes marking flash pages as un-erasable/un-writable. Used to make the RoT immutable. |
| **HDP** (Hide Protection) | Makes a flash region disappear — unreadable even by code — once the RoT hands over. Keeps the app from reading the RoT's keys. |
| **Option bytes (OB)** | Non-volatile configuration of the chip itself (boot address, RDP, WRP, HDP…), separate from the firmware. |
| **Provisioning** | The factory step that programs the RoT, the keys, and the option bytes into a blank chip. |

Everything below is a choice about how to arrange those pieces.

---

## 1. The knobs, at a glance

Each row is an **independent axis**. "This example" = what
`oemirot_dualslot_hwcrypto` ships with.

| # | Axis | Options | This example | Where it's set |
|---|---|---|---|---|
| A | Slot arrangement / install method | single slot · dual-overwrite · dual-swap · bank-swap | **dual-overwrite** | `mcuboot_config.h`, `flash_layout.h`, `example.json` |
| B | Auto-revert on bad firmware | yes · no | **no** | consequence of A |
| C | Anti-rollback (version floor) | yes · no | **yes** | `MCUBOOT_HW_ROLLBACK_PROT` |
| D | Signature algorithm | ECDSA P-256 · P-384 · RSA · Ed25519 | **P-256** | `MCUBOOT_SIGN_EC256` |
| E | Trust anchor stored on device | pubkey hash · full pubkey | **hash** | `MCUBOOT_HW_KEY` |
| F | Number of keys / revocation | 1 key · per-image keys · key + spare for revocation | **1 key** | `keys_map.c`, provisioning XML |
| G | Image encryption | none · AES-128 · AES-256 | **AES-128 (ECIES-P256)** | `MCUBOOT_ENCRYPT_EC256` |
| H | Where the decryption key lives | raw in flash · hardware-wrapped (SAES) | **raw in flash** | `MCUBOOT_RAW_ENC_KEY` |
| I | Crypto engine | software · hardware (PKA/SAES/HASH) | **hardware** | mbedTLS `*_ALT` selection |
| J | Fast boot via hash reference | yes · no | **yes** | `MCUBOOT_USE_HASH_REF` |
| K | Separate data image | yes · no | **no** | `MCUBOOT_DATA_IMAGE_NUMBER` |
| L | Isolation / TrustZone | none · TrustZone / TF-M | **none** | `example.json: isolation/trustzone` |
| M | RDP level in the field | 0 · 2-WBS · 2 | **0** (dev) | `boot_hal_cfg.h`, `provisioning.ini` |
| N | Dev mode | on (logs, stop on error) · off | **on** | `OEMIROT_DEV_MODE` |
| O | Fault-injection hardening | flow control, double-verify, FIH profile | **all on** | `boot_hal_cfg.h`, `mcuboot_config.h` |
| P | Tamper detection | on · off | **on** (erases secrets) | `OEMIROT_TAMPER_ENABLE` |
| Q | Fast wake from Standby | on (skip re-check) · off | **on** | `OEMIROT_FAST_WAKE_UP` |
| R | Where the download lands | internal flash · external flash · no field update | **internal** | `flash_layout.h`, drivers |
| S | Who runs the update agent | the application · a dedicated loader · offline only | **the application** | `appli/fw_update_app.c` |
| T | Device data (calibration, settings) | dedicated region · inside a slot · external | **no region reserved** | `flash_layout.h` |

---

## 2. Each axis in plain language

### 2.1 Axis A — slot arrangement (the big one)

This is the decision everything else bends around. Think of it as: *how many copies of
the firmware do I keep, and how does a new one take over?*

**Single slot.** One copy of the firmware. The RoT verifies it and runs it. There is no
second slot, so a field update must erase the running firmware while writing the new one
— if power fails mid-write, the device is dead until someone reprograms it physically.
*Choose when:* the product is never updated in the field, or is updated only by a
technician with a cable, and you need every last byte of flash.

**Dual slot, overwrite** *(this example)*. Two slots. New firmware is downloaded into the
secondary slot, verified at the next boot, then **copied over** the primary slot. The old
firmware is destroyed in the process. Power-fail safe (the copy simply restarts), but
there is nothing to go back to.
*Choose when:* simplicity matters and you accept that a signed-but-broken firmware
requires a new download to fix.

**Dual slot, swap.** Same two slots, but the RoT *exchanges* the contents instead of
overwriting. The old firmware survives in the secondary slot. The new firmware must
"check in" after it boots (call a confirm function); if it never does — because it
crashed — the next boot **automatically puts the old one back**. This is the classic
safety net.
*Cost:* the swap moves roughly twice as much data and needs trailer space plus a spare
sector to work in. It does **not** need position-independent code: the swap physically
moves the new image *into* the primary slot, so the running image is always in the primary
slot and stays linked for the address it uses today.
*Closer than it looks:* the confirm step already exists in this example's application,
compiled out by `OVERWRITE_ONLY` — see §7 and [`UPDATE_FLOWS.md`](UPDATE_FLOWS.md) §3.

**Bank swap (a.k.a. mirror).** This chip has two 512 KB flash banks and an option byte
(`SWAP_BANK`) that exchanges which bank appears at the boot address. Instead of copying
megabytes, you flip one bit and reset — the other bank becomes the running one instantly.
Elegant and near-instant.
*Caveat, and it is a real one:* the bank swap exchanges the **whole** mapping, including
the address where the RoT itself lives. A design using it must account for that (e.g. a
copy of the RoT in both banks), and this repository contains **no working example of it** —
`SWAP_BANK` appears only as an option byte set to 0. Treat it as "attractive, needs
investigation against the reference manual", not as something you can switch on.

| | Flash used | Auto-revert | Install time | Power-fail safe | In this repo? |
|---|---|---|---|---|---|
| Single slot | 1× | no | n/a | no | no |
| Dual overwrite | 2× | **no** | one full copy | yes | **yes, working** |
| Dual swap | 2× + scratch | **yes** | ~two copies | yes | app side ready, RoT side off |
| Bank swap | 2× (one per bank) | **yes** | instant | yes | **no** — needs design work |

### 2.2 Axis B — auto-revert

Not a free-standing choice: it is *granted by* the slot arrangement. Overwrite cannot
revert. Swap and bank-swap can. If someone says "I want rollback", they are really
choosing axis A.

The question behind it: **if a correctly-signed firmware boots and then fails, who
rescues the device?** Either the bootloader (revert), or a human, or the firmware's own
update agent — which only works if the firmware still runs well enough to accept a
download. See axis S.

### 2.3 Axis C — anti-rollback (the confusingly-named opposite)

Suppose version 1.0 had a security bug fixed in 2.0. An attacker with a copy of the
*genuine, correctly signed* 1.0 image could install it to bring the bug back. Signature
checking does not stop this — 1.0 really is genuine.

The fix is a counter in flash that only ever increases. Each image carries a *security
version*; the RoT refuses anything below the stored counter, and bumps the counter when
it accepts a higher one. This example has it on (`MCUBOOT_HW_ROLLBACK_PROT`, counters in
`boot_nv_counters.c`).

Note the tension with §2.2: anti-rollback deliberately blocks going backwards, auto-revert
deliberately goes backwards. They coexist because revert returns to the image that is
*already installed and already accepted*, not to an arbitrary old one. But raising the
security version aggressively can strand you: once the counter moves, the old image is
refused forever, including as a revert target. Bump the security version only for actual
security fixes.

### 2.4 Axes D, E, F — signing

**D, the algorithm.** ECDSA P-256 is the default and the right one here: the chip has a
PKA accelerator for it. P-384 is stronger and slower. RSA means bigger signatures and
slower verification. Ed25519 is elegant but gets no hardware acceleration on this part.
Post-quantum schemes (LMS, ML-DSA) matter only if the product must outlive a mandate to
migrate — worth a conscious "not now" rather than silence.

**E, what the device stores.** Either the full public key baked into the RoT, or just a
32-byte **hash** of it, with the full key travelling inside the image and checked against
the hash. The hash approach (used here) is smaller and lets each factory batch get a
different key without rebuilding the RoT. Keep it.

**F, how many keys — the irreversible one.** Today: one key for everything. Because the
RoT is immutable, *whatever key arrangement is provisioned is permanent*. If the signing
key is ever compromised and there is no second anchor, every device in the field is
permanently untrustworthy and unpatchable. Options:
- one key (simplest, no recovery from compromise),
- separate keys per image type (app vs. data — limits blast radius),
- a primary key plus a **spare anchor** that can be promoted via an NV counter — the only
  arrangement that survives a key compromise.

This must be decided before provisioning. It cannot be retrofitted.

### 2.5 Axes G, H — encryption

Signing answers "is this firmware genuine?". Encryption answers "can a competitor read my
firmware?". They are independent: you can have either, both, or neither.

If you encrypt, the device needs a decryption key. Today it sits **raw in a flash page** —
protected by HDP and RDP, but plain bytes to anyone who defeats those. The stronger
option on this silicon is to have the SAES peripheral hold a hardware-derived key, so the
usable key never exists in readable memory. That is the most valuable hardening step
available to a "hwcrypto" build, and it is not done yet.

If the firmware is not actually confidential, **dropping encryption** is a legitimate
simplification: it removes a private key from the device entirely.

### 2.6 Axis I — crypto engine

Software (STCryptoLib) or hardware (PKA + SAES + HASH). Hardware is faster and uses half
the scratch RAM (`0x800` vs `0x1000`). That single difference is what separates this
example from its sibling `oemirot_dualslot`. There is no reason to go back to software on
this part unless portability to a chip without those peripherals is required.

### 2.7 Axis J — fast boot via hash reference

Verifying a signature on every single power-up costs time. This optimisation stores the
hash of the already-verified image; on later boots, a matching hash lets the RoT skip the
signature check. Faster boot, one extra flash page, and that page becomes
security-critical (it must stay inside WRP + HDP). Turn it off if boot time is not a
constraint and you prefer the smaller attack surface.

### 2.8 Axis K — separate data image

Certificates, calibration, configuration blobs may need updating independently of the
code. The machinery is present and sized to zero here. Enabling it costs two more slots.

### 2.9 Axis L — isolation

This configuration has no TrustZone: the RoT protects itself with the MPU, hides itself
with HDP, and jumps one-way into the application. That protects the *boot*; it does not
give the running application a secure world for runtime secrets. If the product needs
keys usable at runtime without exposing them, that is a TrustZone/TF-M discussion, and it
changes the flash layout (secure + non-secure slot pairs).

### 2.10 Axis M — RDP level (readout protection)

How hard is it for someone with a debug probe to read your flash?

| Level | Debugger | Can you reprogram the board? | Use |
|---|---|---|---|
| **RDP 0** | full access | yes | **development only** — flash and keys readable by anyone with a cable |
| **RDP 2-WBS** | restricted | via the transition key in `keys/rdp/transition_bs_key.txt` | intermediate; confirm exact semantics in the reference manual |
| **RDP 2** | permanently disabled | **no** | production, final; irreversible |

The RoT is told a *minimum* acceptable level (`OEMIROT_OB_RDP_LEVEL_MIN`) and refuses to
boot below it. This example ships at level 0 with a regression key present — a
development posture. Two hard consequences to internalise before choosing level 2:

- It is **one-way**. No debugger, no reprogramming, no recovery of that board.
- Therefore the field update path must be *proven working* first. Locking a board whose
  update mechanism is broken is how you brick a production run.

### 2.11 Axes N, O, P, Q — hardening and diagnostics

**N, dev mode.** `OEMIROT_DEV_MODE` enables console logging and makes errors *stop* instead
of resetting — excellent for debugging, and it leaks information and hangs the product.
Off in production. Non-negotiable.

**O, fault-injection hardening.** A serious attacker glitches the power or clock to make
the CPU skip the instruction that says "signature invalid". The countermeasures here:
every protection is applied and verified *twice*, a flow-control counter proves no step
was skipped, and signature verification runs twice (`MCUBOOT_DOUBLE_SIGN_VERIF`). Costs
boot time; keep on unless measurements force otherwise.

**P, tamper.** Configured in "confirmed" mode — a tamper event **erases the secrets**.
Correct for security, but understand the false-positive behaviour on your hardware before
shipping; an erased device is not recoverable in the field.

**Q, fast wake-up.** Skips image re-validation when waking from Standby. Only meaningful
if the product uses Standby; it trades a little verification for wake latency.

### 2.12 Axes R, S — where updates come from

**R.** The secondary slot currently sits in internal flash, which is why the application
budget is ~464 KB out of 1 MB. Moving it to external QSPI flash (a `w25q128j` part driver
exists in this repo) would roughly double the usable application size, at the cost of a
board component and a flash driver in the RoT. External images are already encrypted, so
confidentiality survives the move.

**S.** Today the *application* contains the update agent (a YModem menu). This is compact,
but it means a firmware that boots-but-misbehaves may take the update path down with it —
which matters a lot when axis A is "overwrite" (no revert). Alternatives: a small
dedicated loader stage, or ST's Open Bootloader / a DFU path.

### 2.13 Axis T — where device-written data lives

Two different things get called "data", and they need different answers:

- **Device-specific data** — end-of-line calibration, user settings, counters. Written *by
  the device*, different on every unit, must survive every update. This is not MCUboot's
  business at all: it needs a plain flash region **outside both slots**.
- **Manufacturer-delivered data** — certificates, config blobs, tables shipped with a
  release and signed like firmware. That is the data-image feature (axis K), and in swap
  mode it swaps alongside the app.

Anything of the first kind placed *inside* a slot is destroyed by the first update:
overwrite erases the primary slot wholesale, and swap carries the page out to the
secondary slot and hands back whatever sector of the incoming image lands there — then
undoes it on a revert. Mirroring a copy in both slots does not fix this; moving the data
out of the slots does.

The catch in this example: **no region is reserved and there is no free flash.** The two
slots run to `0x100000`. Carving space means shrinking both slots, and since a swap needs
equal slots, **N bytes of data area costs 2N bytes of flash**. A page-aligned example
reserving 16 KB:

| Region | Offset | Size |
|---|---|---|
| primary | `0x18000` | `0x72000` (456 KB) |
| secondary | `0x8A000` | `0x72000` (456 KB) |
| device data | `0xFC000` | `0x4000` (16 KB) |

Storage format matters as much as placement: a single struct rewritten in place loses
everything if power drops during the erase. `oemirot/boot_nv_counters.c` is a compact
model to copy (append-only records with CRC, newest wins, erase only when the page fills);
`middleware/levelx` is the heavier option when the data changes often.

Related constraint — **read-while-write**. On a dual-bank part you generally cannot
execute from a bank while erasing or writing it. Today the application straddles both
banks (the primary slot spills 48 KB past `0x80000`), so a data region cannot simply be
placed "in the other bank". Getting clean RWW means re-laying out so the code sits wholly
in bank 1. Confirm the STM32C5 RWW rules in the reference manual before relying on this.

---

## 3. How many combinations are there, really?

Multiply the options out — 4 slot arrangements × 2 anti-rollback × 4 signature algorithms
× 2 anchor forms × 3 encryption choices × 2 engines × 2 fast-boot × 2 data-image × 2
isolation × 3 RDP levels × 2 dev-mode × 2 wake-up — and you get **roughly 37 000**
nominal configurations.

That number is useless, for two reasons. Most combinations are **illegal** (§4), and of
those that remain, most are **pointless** (nobody wants hardware crypto plus a software
key store plus dev logging in production). What is actually useful is a handful of
coherent profiles (§5).

---

## 4. Rules that eliminate combinations

These are the constraints worth knowing before you draw a matrix. "Impossible" means the
build or the boot will not work; "incoherent" means it works but contradicts itself.

| Rule | Why |
|---|---|
| overwrite + auto-revert → **impossible** | the old image is physically gone |
| single slot + field update via the RoT → **impossible** | nowhere to stage the download |
| direct-XIP + an image bound to one address → **impossible** | direct XIP runs the image where it lies, so it needs position independence or one build per slot. Swap is *not* this case: it moves the image into the primary slot |
| swap without a confirm step in the app → **useless** | every update silently reverts on the next boot |
| bank swap + RoT in only one bank → **broken** | the swap moves the boot address too |
| encryption on + no decryption key provisioned → **impossible** | verification passes, installation fails |
| pubkey-hash anchor + image without the full key in its TLV → **impossible** | nothing to check the hash against |
| hash-ref fast boot + hash-ref page outside WRP/HDP → **incoherent** | the shortcut becomes the attack |
| RDP 2 + dev mode on → **incoherent** | a locked board that prints logs and hangs on error |
| RDP 2 + update path not yet proven → **bricked production run** | no recovery, by design |
| RDP 2 + regression/transition keys still in the flow → **contradictory** | level 2 is one-way |
| aggressive security-version bumps + auto-revert → **traps you** | anti-rollback refuses the revert target |
| tamper "erase secrets" + noisy tamper source → **field failures** | irrecoverable erase on a false positive |
| fast wake-up + product never enters Standby → **dead setting** | no effect |
| hardware crypto + a part without PKA/SAES → **impossible** | software backend exists for exactly this case |
| device-written data inside a slot → **destroyed on first update** | overwrite erases it; swap relocates it and reverts bring it back |
| data region + swap → **costs double** | slots must stay equal, so N bytes reserved removes N from each slot |
| bank swap + a fixed data region → **address moves** | `SWAP_BANK` flips the whole map, including where that region appears |

---

## 5. Realistic complete configurations

This is the list to actually discuss. Each column is a full, self-consistent
configuration — the combinations that are worth considering, rather than all the ones
that are expressible.

| Axis | **P0** Lab | **P1** No field update | **P2** Production overwrite | **P3** Safe update | **P4** Big app | **P5** High assurance |
|---|---|---|---|---|---|---|
| A slots | dual overwrite | single | dual overwrite | dual **swap** | dual, secondary **external** | dual swap |
| B auto-revert | no | n/a | no | **yes** | no | **yes** |
| C anti-rollback | yes | yes | yes | yes | yes | yes |
| D signature | P-256 | P-256 | P-256 | P-256 | P-256 | P-256 (or P-384) |
| E anchor | hash | hash | hash | hash | hash | hash |
| F keys | 1 | 1 | 1 | 1 | 1 | **primary + spare (revocable)** |
| G encryption | AES-128 | optional | AES-128 | AES-128 | AES-128 (**required**) | AES-256 |
| H key storage | raw flash | raw flash | raw flash | raw flash | raw flash | **SAES hardware** |
| I engine | hardware | hardware | hardware | hardware | hardware | hardware |
| J fast boot | yes | yes | yes | yes | yes | your call |
| K data image | no | no | optional | optional | optional | optional |
| L isolation | none | none | none | none | none | **TrustZone** |
| M RDP | **0** | 2 | **2** | **2** | **2** | **2** |
| N dev mode | **on** | off | off | off | off | off |
| O hardening | all on | all on | all on | all on | all on | all on |
| P tamper | on | on | on | on | on | on |
| Q fast wake | on | n/a | per product | per product | per product | per product |
| R download to | internal | n/a | internal | internal | **external QSPI** | internal |
| S update agent | app | none | app | app | app | dedicated loader |
| T device data | none reserved | after the app | carve from both slots | carve from both slots | internal, slots are external | carve from both slots |
| App budget | ~464 KB | ~925 KB | ~464 KB | ~460 KB | ~925 KB | ~460 KB |
| Extra work | **none — ships today** | trim RoT config | provisioning/OB work | enable swap + confirm API | QSPI driver in RoT | SAES + TZ + key strategy |

**P0** is this example, unchanged. **P2** is the smallest honest step to production: same
architecture, dev mode off, RDP raised, keys provisioned for real. **P3** is the one to
pick if a bad-but-signed firmware must not be able to strand a device. **P4** is the
answer if 464 KB is not enough. **P5** is where you end up if the threat model includes a
motivated attacker with physical access.

---

## 6. The order to decide in

Ask these in order; each answer removes whole branches.

1. **Is the firmware updated in the field at all?** No → P1, and most of this document is
   moot. Yes → continue.
2. **If a signed firmware boots and then fails, must the device recover by itself?**
   Yes → swap (P3/P5). No → overwrite (P0/P2/P4).
3. **Does the application fit in ~464 KB?** No → external secondary slot (P4), or
   reconsider step 2. Subtract the device-data region here too (§2.13) — reserving it
   costs twice its size, and retrofitting it later moves every slot boundary.
4. **Is the firmware confidential?** No → drop encryption and one key disappears from the
   device. Yes → decide raw-in-flash vs. SAES-held.
5. **What happens if the signing key leaks?** If "we accept losing the fleet" is not an
   acceptable answer, design key revocation **now** — it cannot be added later.
6. **What is the production lock-down?** RDP level, tamper policy, dev mode off,
   regression allowed or not. Decide early: the option-byte sequences in
   `provisioning/config/example.json` encode it.
7. Everything else (fast boot, fast wake, data image) is tuning and can be revisited.

Steps 5 and 6 are the irreversible ones. They are listed late because the earlier answers
shape them, but they must be **settled before the first device is provisioned**.

---

## 7. Status of each option in this repository

Honesty about what is available versus what needs building:

| Option | Status |
|---|---|
| dual-slot overwrite, hardware crypto, P-256, AES-128, anti-rollback, hash-ref | **working, shipped** — this example |
| software crypto variant | **working** — sibling `oemirot_dualslot` (also covers NUCLEO-C562RE, C542RC) |
| dual-slot swap | **application side already written**, compiled out: `FLASH_PRIMARY_APP_CONFIRM_OFFSET` (`0x8BFE0`) and `FW_UPDATE_ValidAppImage()` + its "Validate app image" menu entry live behind `#if !defined(OVERWRITE_ONLY)`. Missing: the RoT side (`MCUBOOT_SWAP_USING_MOVE` is commented out) and the trailer/spare-sector space the move needs |
| bank swap / mirror | **not present** — `SWAP_BANK` exists only as an option byte set to 0; needs design work |
| data image | plumbing present, sized to 0 — **enable and size the slots** |
| external secondary slot | `w25q128j` part driver exists; **no RoT integration here** |
| SAES-held decryption key | **not implemented** — currently raw key in flash |
| key revocation / multiple anchors | **not implemented** — single anchor in `keys_map.c` |
| TrustZone / isolation | `example.json: isolation false, trustzone false` — **not in this example** |
| region for device-written data | **none reserved** — the slots run to the top of flash |
| RDP 2 production posture | provisioning supports it; example ships at RDP 0 |

Note also: the shared provisioning framework lives in `utilities/rot_provisioning/`, a git
submodule that is **not populated in this checkout** — some of the options above may be
constrained by that framework in ways not visible from these sources alone.
