# Update process — step-by-step schemes for each architecture

Companion to [`DOC.md`](DOC.md) (what this example is) and
[`ARCHITECTURE_CHOICES.md`](ARCHITECTURE_CHOICES.md) (the configuration options).
This file shows **what actually happens, in order, to the bytes in flash** for each of the
candidate architectures.

Diagrams are ASCII so they read identically on GitHub, in the IAR editor and in a plain
terminal. Addresses are the real ones from `flash_layout.h` / `appli_flash_layout.h`.

Legend used throughout:

```
[####]  image present and running        [::::]  image present, not running
[    ]  erased / empty                   [~~~~]  partially written (unsafe)
 M      install-request magic trailer     C      confirmation flag
```

---

## 0. The part that is the same for everyone

Before any architecture-specific behaviour, every update goes through the same pipeline.
Only step 5 onward differs between architectures.

```
   FACTORY (offline, private keys never leave)
   ┌──────────────────────────────────────────────────────────────┐
   │ 1. build appli.hex                                           │
   │ 2. STM32TrustedPackageCreator / imgtool:                     │
   │       • prepend 0x400 header                                 │
   │       • encrypt payload      (AES-128-CTR, key via ECIES)    │
   │       • append TLVs: SHA-256, ECDSA-P256 signature,          │
   │         version 2.0.0, security version, dependencies        │
   │    → appli_fwu_enc_sign.bin                                  │
   └───────────────────────────┬──────────────────────────────────┘
                               │  (any transport: YModem here,
                               │   could be BLE / Ethernet / USB)
   DEVICE                      v
   ┌──────────────────────────────────────────────────────────────┐
   │ 3. running application receives the file                     │
   │ 4. writes it into the DOWNLOAD area                          │
   │ 5. signals "please install"      <-- architecture-specific   │
   │ 6. reset                                                     │
   │ 7. RoT decides what to do        <-- architecture-specific   │
   └──────────────────────────────────────────────────────────────┘
```

**The RoT never downloads anything.** It only ever looks at flash after a reset. All
network/serial code lives in the application. This is deliberate: it keeps the immutable
code small and gives it no attack surface from the outside world.

### What the RoT checks, every boot, before running anything

This sequence is identical in all architectures — only the "install" box differs.

```
 reset
   │
   ├─ apply MPU / tamper / ECC, verify option bytes (WRP, HDP, BOOTADD, RDP)
   │     └─ any mismatch ───────────────────────────► Error_Handler (halt or reset)
   │
   ├─ is there an install request in the download area?
   │     ├─ no  ─────────────────────────────────────┐
   │     └─ yes ─► verify candidate:                 │
   │                 • header well-formed            │
   │                 • ECDSA-P256 signature vs.      │
   │                   pubkey hash in flash          │
   │                 • security version >= NV counter│
   │                 • dependencies satisfied        │
   │               ├─ FAIL ─► discard, keep running old image
   │               └─ OK   ─► INSTALL  (architecture-specific)
   │                                                 │
   ├─ verify the image in the primary slot ◄─────────┘
   │     ├─ hash matches the stored hash reference ─► skip signature check (fast path)
   │     ├─ full ECDSA verification (twice, FIH-hardened)
   │     └─ FAIL ─────────────────────────────────► Error_Handler — nothing runs
   │
   ├─ store hash reference, bump NV counter if needed
   ├─ reduce MPU to the app region, close HDP, disable crypto clocks
   └─ jump to 0x08018400
```

---

## 1. Single slot — no in-field update

```
0x00000  0x12000        0x18000                                 0x100000
   ├────────┼──────────────┼────────────────────────────────────────┤
   │  RoT   │ keys/cnt/hash│            application [####]           │
   └────────┴──────────────┴────────────────────────────────────────┘
                           ~925 KB usable
```

**Update flow:** there isn't one, over the air. A technician connects a probe (only
possible below RDP 2) and reprograms the application region, or the product is never
updated.

```
  technician ──SWD──► erase app region ──► write new image ──► reset ──► RoT verifies ──► runs
                       ▲                                      ▲
                       └─ device is non-functional here ──────┘
                          (power loss = bricked until retried)
```

**Why choose it:** maximum application size, minimum complexity, no update attack surface
at all. **Why not:** no field fixes, and it is incompatible with RDP 2 unless you accept
that a shipped device can never be changed.

---

## 2. Dual slot, overwrite — *this example, as implemented*

```
0x00000    0x12000   0x18000                0x8C000                 0x100000
   ├──────────┼─────────┼──────────────────────┼──────────────────────┤
   │   RoT    │ k/c/h   │   PRIMARY  [####]    │  SECONDARY  [    ]   │
   └──────────┴─────────┴──────────────────────┴──────────────────────┘
                         464 KB, runs here       464 KB, download area
                                                          magic at 0xFFFF0 ┘
```

### Sequence

```
STEP 1  app menu "Download app image"  →  erase secondary slot
        ┌──────────────────┬──────────────────┐
        │ PRIMARY  [####]  │ SECONDARY [    ] │
        └──────────────────┴──────────────────┘

STEP 2  YModem transfer into 0x8C000
        ┌──────────────────┬──────────────────┐
        │ PRIMARY  [####]  │ SECONDARY [::::] │   new image staged, not trusted yet
        └──────────────────┴──────────────────┘

STEP 3  app menu "Request installation of app image"
        writes the 16-byte magic trailer at 0xFFFF0 (end of secondary slot)
        ┌──────────────────┬─────────────────M┐
        │ PRIMARY  [####]  │ SECONDARY [::::] │
        └──────────────────┴──────────────────┘

STEP 4  reset (menu item 1, or any power cycle)

STEP 5  RoT sees the magic, verifies the candidate
        FAIL ─► erase/ignore secondary, boot the old primary  (device stays alive)
        OK   ─► continue

STEP 6  RoT COPIES secondary over primary, decrypting as it goes
        ┌──────────────────┬──────────────────┐
        │ PRIMARY  [~~~~]  │ SECONDARY [::::] │   <-- power loss here is SAFE:
        └──────────────────┴──────────────────┘       the magic is still set, so the
                                                      copy simply restarts next boot

STEP 7  done — old firmware no longer exists anywhere
        ┌──────────────────┬──────────────────┐
        │ PRIMARY  [####]  │ SECONDARY [::::] │   (source copy may remain, inert)
        └──────────────────┴──────────────────┘

STEP 8  RoT re-verifies primary, stores hash ref, bumps NV counter, jumps
```

### Why step 3 exists at all

Downloading the image is not enough, and the extra write is not redundant:

- **The two stages cannot talk.** The RoT runs, hands over, and closes HDP behind it —
  no call back, no API, no shared RAM. The only channel from application to bootloader is
  *leave something in flash, then reset*. "Install this" has to be a mark in flash.
- **"Downloaded" is not "wanted".** Fetching the image and committing to install it are
  two decisions, and the example keeps them apart: *Download app image* (menu 2), then
  *Request installation* (menu 3), then *Reset* (menu 1). Download overnight, install in a
  maintenance window.
- **It proves the transfer finished.** Erased flash reads `0xFF`, and an aborted download
  leaves a slot that looks like a valid beginning. The magic sits *after* the image data,
  so it can only be complete if everything before it was written.
- **It is deliberately not a trust signal.** The application writes it, so it can only say
  "look here" — never "trust this". Verification happens afterwards and rejects anything
  that fails.

Without the flag the RoT would have to guess: re-verify the download slot on every boot,
or install whatever happens to be lying there.

### The failure this architecture cannot handle

```
  new image is correctly signed  ──►  installs fine  ──►  boots  ──►  crashes / hangs
                                                                       │
                                        the old firmware is gone ──────┘
                                        the update menu lived inside the app
                                        └─► no way back without a probe
```

That is the whole trade-off of overwrite mode in one picture. Mitigations: keep the
update agent outside the app (axis S), or move to swap (§3).

---

## 3. Dual slot, swap — with automatic revert

Same two slots, plus two extra pieces of bookkeeping: a **scratch** area used during the
exchange, and a **confirmation flag** the new firmware must set to keep itself.

```
0x18000                     0x8BFE0  0x8C000                      0x100000
   ├───────────────────────────┬C─────┼───────────────────────────────┤
   │        PRIMARY  [####]    │      │      SECONDARY  [    ]      M │
   └──────────────────────────────────┴───────────────────────────────┘
        confirm flag at 0x8BFE0 ┘                 magic at 0xFFFF0 ┘
```

### Sequence

```
STEP 1-4  identical to overwrite: erase, download, magic, reset

STEP 5    RoT verifies the candidate  (same checks)

STEP 6    RoT SWAPS the two slots, sector by sector, via scratch
          ┌──────────────────┬──────────────────┐
          │ PRIMARY  [::::]  │ SECONDARY [####] │   mid-swap; a swap-status record
          └──────────────────┴──────────────────┘   lets it resume after power loss
          result:
          ┌──────────────────┬──────────────────┐
          │ PRIMARY  [NEW ]  │ SECONDARY [OLD ] │   old firmware PRESERVED
          └──────────────────┴──────────────────┘

STEP 7    RoT runs the new image — but marks it "on trial"

STEP 8    the new firmware proves itself:
          app menu "Validate app image" → writes the confirm flag at 0x8BFE0
                     │
          ┌──────────┴───────────────────────────────────────────┐
          │ confirmed                    │ NOT confirmed          │
          │ (flag written)               │ (crash, watchdog,      │
          │                              │  power loss, hang)     │
          v                              v
   next boot: keep it            next boot: RoT swaps BACK
   ┌────────┬────────┐           ┌────────┬────────┐
   │ [NEW ] │ [OLD ] │           │ [OLD ] │ [NEW ] │   device recovers by itself
   └────────┴────────┘           └────────┴────────┘
```

#### Why `0x8BFE0`, and who writes there

It is not an arbitrary address: it is the **last 32 bytes of the primary slot**.
The slot ends at `0x18000 + 0x74000 = 0x8C000`, and MCUboot's trailer is laid out
backwards from that end, one flash programming unit (16 bytes here) per field:

| Address | Field |
|---|---|
| `0x8BFF0` | trailer magic — the final 16 bytes of the slot |
| **`0x8BFE0`** | **`image_ok`** — "this image is confirmed" |
| `0x8BFD0` | `copy_done` |

So `FLASH_PRIMARY_APP_CONFIRM_OFFSET` is simply `image_ok`'s slot in that trailer.

**The application writes it**, into the slot it is itself running from —
`FW_UPDATE_ValidAppImage()` in `appli/fw_update_app.c`, reachable from the
"Validate app image" menu entry. It programs one 16-byte unit: `0x01` followed by
zeros (`const uint8_t FlagPattern[FLASH_PROG_SIZE] = {0x1};`). 16 bytes because that
is the flash's minimum programming granularity on this part, which is also why each
trailer field is padded to 16.

Note the symmetry with the magic trailer, and the difference: the magic goes at the end
of the **secondary** slot and means *"please install this"*; the confirm flag goes at the
end of the **primary** slot and means *"keep what is now running"*.

### Cost of this safety net

- The swap moves roughly **twice** the data of an overwrite → slower install.
- Needs a scratch sector and trailer space in both slots → slightly smaller app budget.
- It does **not** need position-independent code. The swap moves the new image *into* the
  primary slot, so the running image is always there — before, during and after — and
  keeps the link address it has today. (Running an image wherever it happens to sit is
  `MCUBOOT_DIRECT_XIP`, a different mode.)
- **One bootloader, and it never moves.** The RoT stays at `0x00000`; only the two slot
  contents are exchanged. Nothing is duplicated or mirrored.
- The application **must** call the confirm step, or every single update silently reverts.

### What happens to the encrypted image

The application never decrypts anything — it writes the image to the secondary slot
exactly as the signing tool produced it. It could not do otherwise: the decryption key
sits at `0x12000`, inside HDP, which is closed before the application runs.

The repository shows the resulting invariant in its two image recipes:

| | `appli_provisioning_code_image.xml` | `appli_fwu_code_image.xml` |
|---|---|---|
| encryption | `-c` — **no encryption (clear)** | `-E` with the encryption key |
| output | `appli_provisioning_sign.hex` | `appli_fwu_enc_sign.bin` |
| destination | **primary** slot, via the programmer | **secondary** slot, over YModem |

So: **primary slot = plaintext, secondary slot = encrypted.** The RoT unwraps the image's
AES key with the ECIES private key, decrypts on the fly while hashing (the signature is
computed over the *plaintext*, so decryption happens before the image is trusted), and
decrypts again while installing.

#### At which stage the decryption happens

Twice, both inside the bootloader, both during a single install — and never again:

| Stage | In flash | Decryption |
|---|---|---|
| Factory | — | none. The image is **signed first, then encrypted**, so the signature covers the plaintext |
| Download | secondary = ciphertext | none — the app writes bytes it cannot read |
| Key unwrap | — | the ECIES private key unwraps the image's AES key (one asymmetric operation) |
| **Verify candidate** | secondary = ciphertext | **pass 1** — decrypts block by block *in RAM* while hashing. Nothing is written |
| **Install** | primary ← secondary | **pass 2** — decrypts while copying. This one persists |
| Re-verify primary | primary = plaintext | none — hashed directly |
| Every later boot, and runtime | primary = plaintext | none. The crypto clocks are off while the app runs |

Why two passes and not one: verification has to finish *before* installation starts. Pass
1 exists only to reconstruct the hash the signature covers; decrypting straight into the
primary slot would let a forged image overwrite the working firmware before it was found
to be bad.

Plaintext therefore exists in the primary slot (always, once installed), in RAM
(transiently, during the two passes), and nowhere else — never in the secondary slot,
never on the wire. Encryption protects the image in transit and while staged; what
protects the installed image is RDP and WRP.

Swap adds one twist over overwrite: to preserve that invariant, MCUboot **re-encrypts the
outgoing image** as it moves into the secondary slot, and stores the AES key in the image
trailer so the swap can resume after a reset and so a revert still works. Two consequences:

- both slots' trailers need room for the encryption keys — factor it into slot sizing;
- that key lands in a slot trailer, and the slots are **not** covered by HDP
  (`0x00000`–`0x17FFF` only), so on-device code can read it. `MCUBOOT_SWAP_SAVE_ENCTLV`
  stores the ECIES-encrypted TLV instead of the bare key, at the cost of redoing the
  ECIES decrypt on each resume.

This paragraph describes upstream MCUboot behaviour; `middleware/mcuboot` is an
unpopulated submodule in this checkout, so it could not be verified against ST's `hal2`
fork. Confirm there before relying on the details.

> **Already present in this repository:** the confirm mechanism is written and compiled
> out, not missing. `appli_flash_layout.h` defines `FLASH_PRIMARY_APP_CONFIRM_OFFSET`
> (`0x8BFE0`) under `#if !defined(OVERWRITE_ONLY)`, and `fw_update_app.c` has
> `FW_UPDATE_ValidAppImage()` plus the "Validate app image" menu entry behind the same
> guard. The tooling and the application side of swap mode are in place; what is not
> exercised here is the RoT side (`MCUBOOT_SWAP_USING_MOVE` is commented out in
> `mcuboot_config.h`) and the trailer plus spare-sector space the move needs.

---

## 4. Bank swap (mirror) — instant install

> **Not the same thing as §3.** Dual-slot swap is software exchanging two slot contents,
> with one bootloader that never moves. Bank swap is the *hardware* flipping the whole
> address map. Only this second one raises the "two copies of the RoT" problem below.

The chip has two 512 KB banks and an option byte, `SWAP_BANK`, that exchanges which bank
is mapped at the boot address. Instead of moving the firmware, you move the *map*.

```
   SWAP_BANK = 0                          SWAP_BANK = 1
   ┌─────────────┐ 0x08000000             ┌─────────────┐ 0x08000000
   │   BANK 1    │  ← runs from here      │   BANK 2    │  ← now runs from here
   │  [####]     │                        │  [NEW ]     │
   ├─────────────┤ 0x08080000             ├─────────────┤ 0x08080000
   │   BANK 2    │  ← staged here         │   BANK 1    │  ← previous, preserved
   │  [NEW ]     │                        │  [####]     │
   └─────────────┘                        └─────────────┘

              one option-byte write + reset, no copying
```

### Sequence

```
STEP 1-3  download into the inactive bank, request install
STEP 4    reset
STEP 5    RoT verifies the candidate in the inactive bank
STEP 6    RoT writes the SWAP_BANK option byte  ──► install time ≈ 0
STEP 7    reset; the banks are exchanged; the new firmware runs
STEP 8    confirm-or-revert works exactly as in §3, but reverting is
          another option-byte flip instead of another copy
```

### The catch you must resolve first

`SWAP_BANK` exchanges the **entire** bank mapping — including `0x08000000`, where the RoT
itself lives. A second obstacle: the current slots are not bank-contained — the primary
slot spills 48 KB past the `0x80000` boundary into bank 2 — so a mirror scheme needs a
re-layout before anything else. And any fixed region of device data would appear at a
different address after the flip. Flipping it moves the bootloader too. A working mirror design therefore has
to answer: *where does the immutable RoT live such that it is still at the boot address
after the swap?* (An identical copy in both banks is the usual answer, costing 72 KB
twice, and both copies must be WRP-protected.)

### What you would have to mirror

The flip moves every address, so anything at a fixed address needs a copy in both banks:

| | Mirrored? | Why |
|---|---|---|
| Bootloader (RoT) | **yes — two identical copies** | whichever bank lands low needs a working RoT at offset 0 |
| Application | **no** | the banks hold *different* images, new and old — that is the point |
| Keys (pubkey hash, decryption key) | yes, harmlessly | they never change, so the copies stay identical |
| NV counters (anti-rollback) | yes — **and that is a problem** | written at runtime, so the copies drift apart |
| Hash references | yes, and they go stale | the inactive bank's cache does not match the running image |
| Calibration / configuration | yes, and worse | the *application* writes it, so a write after a flip lands in one bank only |
| Install-request flag | mechanism changes entirely | there is no "secondary slot" to put a trailer at the end of |

Duplicating something immutable is free. Duplicating something written at runtime means
the copies diverge — an annoyance for calibration, and a **security hole** for the
anti-rollback counter: flip to the bank holding the older counter and the floor drops.
There is no "outside the swapped region" to escape to, since `SWAP_BANK` exchanges the
whole user flash; the realistic homes for device data are external EEPROM or flash.

And the doubled RoT comes out of the application budget:

| | RoT overhead | App budget |
|---|---|---|
| Dual-slot swap | 96 KB, shared | **~456 KB** |
| Bank swap | 192 KB (96 per bank) | **416 KB** |

So bank swap buys install speed at the price of ~40 KB *less* application space, no clean
home for device data, and a counter-coherency problem to solve.

**Status: not implemented anywhere in this repository.** `SWAP_BANK` appears only as a
static option byte set to `0` in `provisioning/config/example.json`. Everything above is
how such a design would work, not something that can be switched on. Verify against the
STM32C5 reference manual before committing to it.

---

## 5. External download slot — a variant, not a fifth architecture

Orthogonal to §2/§3: keep the install mechanics, move the *staging area* off-chip.

```
   INTERNAL 1 MB                              EXTERNAL QSPI
   ┌────────┬──────┬────────────────────┐     ┌────────────────────┐
   │  RoT   │ k/c/h│  PRIMARY  [####]   │     │ SECONDARY  [::::]  │
   └────────┴──────┴────────────────────┘     └────────────────────┘
                     ~925 KB usable              download lands here
```

```
STEP 1-3  app downloads into external flash, sets the install request
STEP 4    reset
STEP 5    RoT reads the candidate OVER QSPI, verifies it in place
STEP 6    RoT decrypts and copies external → internal primary
STEP 7-8  as in §2
```

- Roughly **doubles** the application budget (~464 KB → ~925 KB).
- The RoT grows a QSPI driver — more immutable code, more to get right.
- Confidentiality still holds: the staged image is encrypted, and external flash is
  assumed readable by an attacker anyway.
- `part_drivers/w25q128j` exists in this repository; **the RoT integration does not**.

---

## 6. Side-by-side

| | Single slot | **Overwrite** | Swap | Bank swap | External |
|---|---|---|---|---|---|
| App budget | ~925 KB | **~464 KB** | ~460 KB | ~460 KB | ~925 KB |
| Install time | n/a | one copy | ~two copies | **≈ 0** | one copy + QSPI read |
| Old firmware after install | gone | **gone** | preserved | preserved | gone |
| Auto-revert on crash | no | **no** | **yes** | **yes** | no |
| App must confirm | no | **no** | **yes** | yes | no |
| Image link address | primary | primary | **primary** (unchanged) | same address in both banks | primary |
| Extra flash structures | — | magic | magic + confirm + scratch | magic + confirm + OB | magic |
| Status here | not built | **works today** | app side ready, RoT side off | not implemented | driver only |

### Power loss, per step

| Interrupted during… | Single | Overwrite | Swap | Bank swap |
|---|---|---|---|---|
| download | harmless, redo | harmless, redo | harmless, redo | harmless, redo |
| writing the install request | harmless (incomplete magic is ignored) | same | same | same |
| **the install itself** | **BRICK** | safe — copy restarts | safe — swap status resumes | safe — OB write is atomic |
| first boot of the new image | n/a | stuck on new image | **auto-reverts** | **auto-reverts** |

### What happens to a bad image, by failure type

| Failure | Overwrite | Swap / bank swap |
|---|---|---|
| Wrong/forged signature | rejected before install; old image keeps running | same |
| Version below the anti-rollback counter | rejected before install | same |
| Corrupted during transfer | hash mismatch → rejected | same |
| Correctly signed but **crashes at runtime** | **device stuck — needs a probe** | reverts automatically on next boot |
| Correctly signed, runs, but breaks the update path | **device stuck** | reverts automatically |

The last two rows are the entire argument for swap mode.

---

## 7. Which flow to walk through with someone new

Start at §2 — it is the one that runs on the board today, and every other scheme is a
variation on it. Then §3, because the difference between §2 and §3 (one confirmation flag)
is the difference between "a bad firmware bricks the device" and "the device fixes
itself", and that is the decision most worth making deliberately.
