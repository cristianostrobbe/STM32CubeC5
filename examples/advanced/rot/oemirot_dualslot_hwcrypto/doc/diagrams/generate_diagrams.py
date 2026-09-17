#!/usr/bin/env python3
"""
Generate presentation-ready diagrams for the OEMiRoT dual-slot (hwcrypto) example.

Outputs:
  svg/*.svg   vector, drop straight into PowerPoint (Insert > Picture, then
              optionally right-click > Convert to Shape to recolour)
  png/*.png   2x raster fallback for templates/tools that dislike SVG

Usage:  python3 generate_diagrams.py [--no-png]

Backgrounds are transparent so the diagrams sit on any light slide master.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SVG_DIR = os.path.join(HERE, "svg")
PNG_DIR = os.path.join(HERE, "png")

W, H = 1600, 900
FONT = "Segoe UI, Arial, Helvetica, sans-serif"
MONO = "Consolas, Menlo, monospace"

# ---------------------------------------------------------------- palette ---
INK       = "#03234B"   # ST navy - primary ink
INK_SOFT  = "#5B6B80"
CYAN      = "#3CB4E6"   # ST light blue - staged / new
CYAN_DK   = "#1B7CA8"
CYAN_LT   = "#E4F4FC"
GREEN     = "#12A05C"   # running / good
GREEN_LT  = "#E2F5EC"
AMBER     = "#E08A1E"   # in progress / caution
AMBER_LT  = "#FDF1DE"
RED       = "#D0323C"   # rejected / dead end
RED_LT    = "#FBE7E8"
VIOLET    = "#6B5BD2"   # keys & metadata
VIOLET_LT = "#ECE9FB"
GRAY_LT   = "#EFF3F7"
GRAY_BD   = "#C6D0DB"
WHITE     = "#FFFFFF"


# ------------------------------------------------------------- primitives ---
def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def header(w=W, h=H):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"
     viewBox="0 0 {w} {h}" font-family="{FONT}">
<defs>
  <marker id="ar" markerWidth="11" markerHeight="8" refX="10" refY="4"
          orient="auto" markerUnits="userSpaceOnUse">
    <path d="M0,0 L11,4 L0,8 Z" fill="context-stroke"/>
  </marker>
  <marker id="arInk" markerWidth="11" markerHeight="8" refX="10" refY="4"
          orient="auto" markerUnits="userSpaceOnUse">
    <path d="M0,0 L11,4 L0,8 Z" fill="{INK}"/>
  </marker>
  <marker id="arRed" markerWidth="11" markerHeight="8" refX="10" refY="4"
          orient="auto" markerUnits="userSpaceOnUse">
    <path d="M0,0 L11,4 L0,8 Z" fill="{RED}"/>
  </marker>
  <marker id="arGreen" markerWidth="11" markerHeight="8" refX="10" refY="4"
          orient="auto" markerUnits="userSpaceOnUse">
    <path d="M0,0 L11,4 L0,8 Z" fill="{GREEN}"/>
  </marker>
  <marker id="arCyan" markerWidth="11" markerHeight="8" refX="10" refY="4"
          orient="auto" markerUnits="userSpaceOnUse">
    <path d="M0,0 L11,4 L0,8 Z" fill="{CYAN_DK}"/>
  </marker>
  <pattern id="hatch" width="9" height="9" patternTransform="rotate(45)"
           patternUnits="userSpaceOnUse">
    <rect width="9" height="9" fill="{AMBER_LT}"/>
    <line x1="0" y1="0" x2="0" y2="9" stroke="{AMBER}" stroke-width="3.5" opacity="0.55"/>
  </pattern>
  <pattern id="hatchGray" width="9" height="9" patternTransform="rotate(45)"
           patternUnits="userSpaceOnUse">
    <rect width="9" height="9" fill="{GRAY_LT}"/>
    <line x1="0" y1="0" x2="0" y2="9" stroke="{GRAY_BD}" stroke-width="3.5"/>
  </pattern>
</defs>
'''


def close():
    return "</svg>\n"


def text(x, y, s, size=22, fill=INK, anchor="middle", weight="400",
         family=None, opacity=1.0, spacing=None):
    f = family or FONT
    sp = f' letter-spacing="{spacing}"' if spacing else ""
    op = f' opacity="{opacity}"' if opacity != 1.0 else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}" '
            f'font-family="{f}"{sp}{op}>{esc(s)}</text>\n')


def rect(x, y, w, h, fill=WHITE, stroke=None, rx=12, sw=2, dash=None, opacity=1.0):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    da = f' stroke-dasharray="{dash}"' if dash else ""
    op = f' opacity="{opacity}"' if opacity != 1.0 else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}"{st}{da}{op}/>\n')


def line(x1, y1, x2, y2, color=INK, sw=2.5, dash=None, marker=None, opacity=1.0):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    mk = f' marker-end="url(#{marker})"' if marker else ""
    op = f' opacity="{opacity}"' if opacity != 1.0 else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="{sw}" stroke-linecap="round"{da}{mk}{op}/>\n')


def path(d, stroke=INK, fill="none", sw=2.5, dash=None, marker=None, opacity=1.0):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    mk = f' marker-end="url(#{marker})"' if marker else ""
    op = f' opacity="{opacity}"' if opacity != 1.0 else ""
    return (f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round"{da}{mk}{op}/>\n')


def title_block(t, sub=None, x=64, y=74):
    o = text(x, y, t, size=38, weight="700", anchor="start")
    if sub:
        o += text(x, y + 36, sub, size=21, fill=INK_SOFT, anchor="start")
    return o


def chip(x, y, label, fill=CYAN_LT, stroke=CYAN_DK, tcol=INK, size=17, pad=22, h=36):
    w = len(label) * size * 0.60 + pad * 2
    o = rect(x, y, w, h, fill=fill, stroke=stroke, rx=h / 2, sw=1.6)
    o += text(x + w / 2, y + h / 2 + size * 0.36, label, size=size, fill=tcol, weight="600")
    return o, w


def step_dot(x, y, n, color=INK, r=21, tcol=WHITE):
    o = f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>\n'
    o += text(x, y + 7.5, str(n), size=21, fill=tcol, weight="700")
    return o


def check(x, y, color=GREEN, s=1.0):
    return path(f"M{x-9*s},{y} L{x-2*s},{y+7*s} L{x+10*s},{y-8*s}",
                stroke=color, sw=4 * s)


def cross(x, y, color=RED, s=1.0):
    return (path(f"M{x-8*s},{y-8*s} L{x+8*s},{y+8*s}", stroke=color, sw=4 * s) +
            path(f"M{x+8*s},{y-8*s} L{x-8*s},{y+8*s}", stroke=color, sw=4 * s))


def card(x, y, w, h, title=None, fill=WHITE, stroke=GRAY_BD, rx=16, sw=2,
         tsize=22, tcol=INK):
    o = rect(x, y, w, h, fill=fill, stroke=stroke, rx=rx, sw=sw)
    if title:
        o += text(x + w / 2, y + 34, title, size=tsize, fill=tcol, weight="700")
    return o


# --------------------------------------------------------- slot primitives ---
STATE = {
    "run":    (GREEN_LT, GREEN,   "RUNNING"),
    "new":    (CYAN_LT,  CYAN_DK, "NEW IMAGE"),
    "old":    ("url(#hatchGray)", GRAY_BD, "PREVIOUS"),
    "staged": (CYAN_LT,  CYAN_DK, "STAGED — not trusted yet"),
    "empty":  (GRAY_LT,  GRAY_BD, "ERASED"),
    "copy":   ("url(#hatch)", AMBER, "COPY IN PROGRESS"),
    "gone":   (GRAY_LT,  GRAY_BD, "inert copy"),
}


def slot(x, y, w, h, state, name, note=None, tag=None):
    fill, stroke, label = STATE[state]
    dash = "7 6" if state in ("empty", "gone") else None
    o = rect(x, y, w, h, fill=fill, stroke=stroke, rx=10, sw=2.4, dash=dash)
    o += text(x + w / 2, y + h / 2 - 6, name, size=19, fill=INK, weight="700")
    lbl = note if note is not None else label
    o += text(x + w / 2, y + h / 2 + 20, lbl, size=16,
              fill=INK_SOFT if state in ("empty", "gone", "old") else stroke,
              weight="600")
    if tag:
        tw = len(tag) * 9.6 + 20
        o += rect(x + w - tw - 10, y - 13, tw, 26, fill=VIOLET, stroke=None, rx=13)
        o += text(x + w - tw / 2 - 10, y + 5, tag, size=15, fill=WHITE, weight="700")
    return o


def slot_pair(x, y, w, h, s1, s2, n1="PRIMARY SLOT", n2="SECONDARY SLOT",
              note1=None, note2=None, tag1=None, tag2=None, gap=14):
    sw_ = (w - gap) / 2
    return (slot(x, y, sw_, h, s1, n1, note1, tag1) +
            slot(x + sw_ + gap, y, sw_, h, s2, n2, note2, tag2))


def write(name, body, w=W, h=H):
    os.makedirs(SVG_DIR, exist_ok=True)
    p = os.path.join(SVG_DIR, name + ".svg")
    with open(p, "w") as f:
        f.write(header(w, h) + body + close())
    return p


# =============================================================== diagram 1 ===
def d01_two_stage_boot():
    o = title_block("Secure boot: two stages, one door that only opens forwards",
                    "OEMiRoT verifies the application on every reset — then hides itself before handing over")
    y = 200
    o += step_dot(110, y + 96, "", color=INK, r=44)
    o += text(110, y + 88, "RESET", size=17, fill=WHITE, weight="700")
    o += text(110, y + 110, "BOOTADD", size=13, fill=CYAN, weight="600")
    o += line(158, y + 96, 218, y + 96, color=INK, sw=3, marker="arInk")

    # RoT block
    o += card(228, y, 700, 300, fill=WHITE, stroke=INK, sw=3)
    o += rect(228, y, 700, 58, fill=INK, stroke=None, rx=16)
    o += rect(228, y + 40, 700, 18, fill=INK, stroke=None, rx=0)
    o += text(578, y + 38, "OEMiRoT   —   immutable root of trust", size=24,
              fill=WHITE, weight="700")
    steps = [
        ("Apply protections", "MPU · tamper · ECC · caches"),
        ("Check option bytes", "BOOTADD · BOOT_LOCK · WRP · HDP · RDP"),
        ("Verify the application", "SHA-256 + ECDSA P-256, twice (fault-injection hardened)"),
        ("Close the door", "shrink MPU · close HDP · disable crypto clocks"),
    ]
    for i, (a, b) in enumerate(steps):
        yy = y + 78 + i * 55
        o += step_dot(268, yy + 20, i + 1, color=CYAN_DK, r=17)
        o += text(298, yy + 15, a, size=20, weight="700", anchor="start")
        o += text(298, yy + 37, b, size=16, fill=INK_SOFT, anchor="start")

    o += line(938, y + 150, 1008, y + 150, color=GREEN, sw=3.5, marker="arGreen")
    o += text(973, y + 132, "verified", size=16, fill=GREEN, weight="700")
    o += text(973, y + 182, "jump", size=16, fill=GREEN, weight="700")

    o += card(1018, y + 60, 300, 180, fill=GREEN_LT, stroke=GREEN, sw=3)
    o += text(1168, y + 112, "APPLICATION", size=25, weight="700")
    o += text(1168, y + 146, "0x08018400", size=19, fill=GREEN,
              weight="700", family=MONO)
    o += text(1168, y + 182, "updatable firmware", size=17, fill=INK_SOFT)
    o += text(1168, y + 208, "carries the update agent", size=17, fill=INK_SOFT)

    # one-way annotation
    o += rect(228, 566, 1090, 78, fill=VIOLET_LT, stroke=VIOLET, rx=14, sw=2)
    o += text(258, 601, "After the jump the RoT code and the keys are GONE from the map (HDP).",
              size=19, weight="700", anchor="start", fill=INK)
    o += text(258, 629, "The application cannot read them, cannot call back, and cannot modify the boot stage. "
                        "Only a reset returns to the RoT.",
              size=17, fill=INK_SOFT, anchor="start")

    bx = 228
    for lbl, col, colbg in (("Immutable — write-protected (WRP)", INK, GRAY_LT),
                            ("Hidden after boot (HDP)", VIOLET, VIOLET_LT),
                            ("Re-verified on every reset", GREEN, GREEN_LT)):
        c, w_ = chip(bx, 686, lbl, fill=colbg, stroke=col, size=17)
        o += c
        bx += w_ + 16
    o += text(64, 812, "Any failed check ends at Error_Handler — the application simply never runs.",
              size=19, fill=RED, weight="600", anchor="start")
    return write("01-two-stage-boot", o)


# =============================================================== diagram 2 ===
def d02_flash_map():
    o = title_block("Where everything lives — 1 MB of flash",
                    "STM32C5A3ZG · two 512 KB banks · 8 KB pages · offsets from flash_layout.h")
    x0, wtot, y, bh = 64, 1472, 252, 122
    kb = wtot / 1024.0
    segs = [("RoT code", "", 72, INK, 17),
            ("", "", 24, VIOLET, 0),
            ("PRIMARY SLOT", "the firmware that runs", 464, GREEN, 23),
            ("SECONDARY SLOT", "download area", 464, CYAN_DK, 23)]
    x = x0
    for name, sub, size_kb, fill, fs in segs:
        w = size_kb * kb
        o += rect(x, y, w, bh, fill=fill, stroke=None, rx=8)
        if fs:
            o += text(x + w / 2, y + (bh / 2 + 6 if not sub else bh / 2 - 4),
                      name, size=fs, fill=WHITE, weight="700")
            if sub:
                o += text(x + w / 2, y + bh / 2 + 26, sub, size=17,
                          fill=WHITE, opacity=0.85)
        x += w

    # offsets above (only the ones that fit; the metadata offsets live in the zoom panel)
    for off, lbl in ((0, "0x00000"), (96, "0x18000"), (560, "0x8C000"), (1024, "0x100000")):
        xx = x0 + off * kb
        anc = "start" if off == 0 else ("end" if off == 1024 else "middle")
        o += line(xx, y - 14, xx, y, color=INK_SOFT, sw=1.6)
        o += text(xx, y - 24, lbl, size=17, fill=INK_SOFT, weight="600",
                  family=MONO, anchor=anc)

    xb = x0 + 512 * kb
    o += line(xb, y - 52, xb, y + bh, color=RED, sw=2.4, dash="8 6")
    o += text(xb, y - 60, "bank 1  |  bank 2", size=17, fill=RED, weight="700")

    o += text(x0 + 36 * kb, y + bh + 30, "72 KB", size=18, weight="700")
    o += text(x0 + 328 * kb, y + bh + 30, "464 KB", size=18, weight="700")
    o += text(x0 + 792 * kb, y + bh + 30, "464 KB", size=18, weight="700")

    # protection brackets, below the bar, labels to the right so nothing clips
    def bracket(xa, xb_, yy, label, color, lx):
        s = path(f"M{xa},{yy-12} L{xa},{yy} L{xb_},{yy} L{xb_},{yy-12}",
                 stroke=color, sw=2.6)
        s += line(xb_ + 8, yy, lx - 12, yy, color=color, sw=1.4, dash="3 5", opacity=0.7)
        s += text(lx, yy + 6, label, size=18, fill=color, weight="700", anchor="start")
        return s
    o += bracket(x0, x0 + 80 * kb, y + bh + 66, "WRP — cannot be erased or written",
                 INK, 640)
    o += bracket(x0, x0 + 96 * kb, y + bh + 124, "HDP — invisible once the application runs",
                 VIOLET, 640)

    # zoom on the metadata band
    zx, zy, zw, zh = 300, 604, 720, 196
    mx1, mx2 = x0 + 72 * kb, x0 + 96 * kb
    o += path(f"M{mx1},{y+bh} L{zx},{zy}", stroke=VIOLET, sw=1.8, dash="6 6", opacity=0.7)
    o += path(f"M{mx2},{y+bh} L{zx+zw},{zy}", stroke=VIOLET, sw=1.8, dash="6 6", opacity=0.7)
    o += rect(mx1, y, mx2 - mx1, bh, fill="none", stroke=VIOLET, sw=3, rx=4)
    o += card(zx, zy, zw, zh, fill=VIOLET_LT, stroke=VIOLET, sw=2.4)
    o += text(zx + zw / 2, zy + 38, "the 24 KB the RoT keeps for itself",
              size=21, weight="700")
    items = [("0x12000", "keys", "hash of the signing public key + the decryption key"),
             ("0x14000", "counters", "anti-rollback floor — refuses older firmware"),
             ("0x16000", "hash refs", "lets a known-good image skip the signature check")]
    for i, (a, b, c) in enumerate(items):
        yy = zy + 82 + i * 38
        o += text(zx + 26, yy, a, size=17, fill=VIOLET, weight="700",
                  anchor="start", family=MONO)
        o += text(zx + 136, yy, b, size=17, weight="700", anchor="start")
        o += text(zx + 258, yy, c, size=16, fill=INK_SOFT, anchor="start")

    o += rect(64, 832, 1472, 2, fill=GRAY_BD)
    o += text(64, 874, "Two slots of the same size is what makes a safe update possible — and it is why the app budget is 464 KB, not 925 KB.",
              size=20, weight="600", anchor="start")
    return write("02-flash-map", o)


# =============================================================== diagram 3 ===
def d03_pipeline():
    o = title_block("From build to running firmware",
                    "The bootloader never downloads anything — it only ever looks at flash after a reset")
    zones = [("IN THE FACTORY", 64, 470, VIOLET, "private keys never leave"),
             ("IN THE FIELD", 566, 300, AMBER, "any transport you like"),
             ("ON THE DEVICE", 898, 638, GREEN, "the only place trust is decided")]
    for name, x, w, col, sub in zones:
        o += rect(x, 168, w, 560, fill=WHITE, stroke=col, rx=18, sw=2.4, dash="9 7")
        o += rect(x + 22, 152, len(name) * 11 + 34, 32, fill=col, rx=16)
        o += text(x + 22 + (len(name) * 11 + 34) / 2, 174, name, size=16,
                  fill=WHITE, weight="700")
        o += text(x + w / 2, 714, sub, size=16, fill=col, weight="600")

    def stepbox(x, y, w, h, n, t, sub, col, colbg):
        s = card(x, y, w, h, fill=colbg, stroke=col, sw=2.2)
        s += step_dot(x + 34, y + 34, n, color=col, r=18)
        s += text(x + 64, y + 30, t, size=20, weight="700", anchor="start")
        for i, ln in enumerate(sub):
            s += text(x + 64, y + 58 + i * 24, ln, size=16, fill=INK_SOFT, anchor="start")
        return s

    o += stepbox(90, 205, 418, 118, 1, "Build", ["appli.hex — plain firmware"], VIOLET, WHITE)
    o += stepbox(90, 345, 418, 200, 2, "Sign and encrypt",
                 ["prepend a 0x400 header",
                  "encrypt the payload (AES-128)",
                  "append signature TLV (ECDSA P-256),",
                  "version, security version, hashes"], VIOLET, VIOLET_LT)
    o += text(299, 588, "appli_fwu_enc_sign.bin", size=18, fill=VIOLET,
              weight="700", family=MONO)
    o += text(299, 616, "safe to publish — it is encrypted and signed", size=15, fill=INK_SOFT)

    o += stepbox(590, 275, 252, 150, 3, "Deliver",
                 ["YModem here —", "BLE, USB, Ethernet", "would work the same"], AMBER, AMBER_LT)
    o += line(510, 350, 586, 350, color=AMBER, sw=3, marker="ar")
    o += line(846, 350, 918, 350, color=AMBER, sw=3, marker="ar")

    o += stepbox(922, 205, 590, 104, 4, "The app stages it",
                 ["erase the secondary slot, write the image into it"], GREEN, WHITE)
    o += stepbox(922, 325, 590, 104, 5, "The app asks for it",
                 ["write the magic trailer at the end of the slot"], GREEN, WHITE)
    o += stepbox(922, 445, 590, 84, 6, "Reset", [], GREEN, WHITE)
    o += stepbox(922, 545, 590, 136, 7, "The RoT decides",
                 ["verify the candidate · install it · verify again",
                  "bump the anti-rollback counter · run it"], GREEN, GREEN_LT)

    o += rect(64, 762, 1472, 76, fill=GRAY_LT, stroke=GRAY_BD, rx=14, sw=2)
    o += text(90, 794, "Why this split matters: all the network code lives in the replaceable application.",
              size=20, weight="700", anchor="start")
    o += text(90, 822, "The immutable part stays small, offline, and has no attack surface facing the outside world.",
              size=18, fill=INK_SOFT, anchor="start")
    return write("03-update-pipeline", o)


# =============================================================== diagram 4 ===
def d04_boot_decision():
    o = title_block("What the bootloader does on every single reset",
                    "Three ways to be rejected — and nothing runs until the signature checks out")
    cx, bw = 470, 560

    def node(y_, t, sub=None, fill=WHITE, stroke=INK, h=66, tcol=INK):
        s = card(cx - bw / 2, y_, bw, h, fill=fill, stroke=stroke, sw=2.4)
        s += text(cx, y_ + (32 if sub else h / 2 + 8), t, size=21, weight="700", fill=tcol)
        if sub:
            s += text(cx, y_ + 54, sub, size=15,
                      fill=INK_SOFT if tcol == INK else tcol, opacity=0.95)
        return s

    def down(y1, y2, label=None):
        s = line(cx, y1, cx, y2, color=INK, sw=2.6, marker="arInk")
        if label:
            s += text(cx + 16, (y1 + y2) / 2 + 6, label, size=16,
                      fill=GREEN, weight="700", anchor="start")
        return s

    def reject(y_, tag, head, why):
        s = line(cx + bw / 2, y_, 1042, y_, color=RED, sw=2.6, dash="7 5", marker="arRed")
        s += text(cx + bw / 2 + 16, y_ - 12, tag, size=16, fill=RED,
                  weight="700", anchor="start")
        s += card(1052, y_ - 38, 484, 76, fill=RED_LT, stroke=RED, sw=2)
        s += text(1076, y_ - 6, head, size=19, weight="700", anchor="start")
        s += text(1076, y_ + 20, why, size=15, fill=INK_SOFT, anchor="start")
        return s

    o += node(158, "RESET", fill=INK, stroke=INK, h=54, tcol=WHITE)
    o += down(212, 248)
    o += node(248, "Apply protections, check option bytes",
              "MPU · tamper · WRP · HDP · RDP · boot address")
    o += reject(281, "mismatch", "Chip not in the expected state",
                "someone changed the option bytes — halt")
    o += down(314, 350)
    o += node(350, "Is an install requested?",
              "magic trailer at the end of the secondary slot?",
              fill=CYAN_LT, stroke=CYAN_DK)
    o += down(416, 452, "yes")
    o += node(452, "Verify the candidate",
              "signature · version ≥ anti-rollback floor · dependencies",
              fill=CYAN_LT, stroke=CYAN_DK)
    o += reject(485, "fail", "Candidate refused",
                "forged, corrupted or too old — the old image keeps running")
    o += down(518, 554)
    o += node(554, "INSTALL", "overwrite · swap · bank flip — see the next slides",
              fill=AMBER_LT, stroke=AMBER)
    o += down(620, 656)
    o += node(656, "Verify what sits in the primary slot",
              "hash reference matches? skip · otherwise verify in full, twice",
              fill=GREEN_LT, stroke=GREEN)
    o += reject(689, "fail", "Nothing runs",
                "a tampered primary slot is never executed")
    o += down(722, 758)
    o += node(758, "Close HDP · disable crypto · JUMP",
              fill=GREEN, stroke=GREEN, h=54, tcol=WHITE)

    # the "no install requested" bypass: straight to the primary-slot check
    o += path(f"M{cx-bw/2},383 L150,383 L150,689 L{cx-bw/2-6},689",
              stroke=INK_SOFT, sw=2.4, dash="7 5", marker="arInk")
    o += text(186, 372, "no", size=16, fill=INK_SOFT, weight="700", anchor="end")
    o += text(178, 752, "the ordinary boot —", size=15, fill=INK_SOFT, anchor="end")
    o += text(178, 774, "no update pending", size=15, fill=INK_SOFT, anchor="end")
    return write("04-boot-decision", o)


# =============================================================== diagram 5 ===
def d05_overwrite():
    o = title_block("Dual slot, OVERWRITE — what runs on the board today",
                    "The new image is copied over the old one. Simple, power-fail safe, and there is no way back.")
    rows = [
        (1, "The app erases the download area", "run", "empty", None, None, None),
        (2, "YModem writes the new image into it", "run", "staged", None, None, None),
        (3, "The app writes the magic trailer", "run", "staged", None, None, "MAGIC @ 0xFFFF0"),
        (4, "Reset — the RoT verifies, then copies", "copy", "staged", None, None, None),
        (5, "Done — the old firmware no longer exists", "run", "gone", None, None, None),
    ]
    y = 190
    for n, cap, s1, s2, n1, n2, tag in rows:
        o += step_dot(96, y + 40, n, color=INK)
        o += text(132, y + 16, cap, size=20, weight="700", anchor="start")
        o += slot_pair(132, y + 30, 1000, 74, s1, s2, tag2=tag)
        y += 118

    o += card(1174, 190, 362, 214, fill=GREEN_LT, stroke=GREEN, sw=2.4)
    o += check(1220, 232, GREEN, 1.1)
    o += text(1246, 240, "Power loss is safe", size=20, weight="700", anchor="start")
    o += text(1200, 278, "The magic trailer is still set,", size=16, fill=INK_SOFT, anchor="start")
    o += text(1200, 302, "so the copy simply starts again", size=16, fill=INK_SOFT, anchor="start")
    o += text(1200, 326, "at the next boot. The device", size=16, fill=INK_SOFT, anchor="start")
    o += text(1200, 350, "cannot be bricked mid-install.", size=16, fill=INK_SOFT, anchor="start")

    o += card(1174, 424, 362, 234, fill=RED_LT, stroke=RED, sw=2.4)
    o += cross(1220, 466, RED, 1.0)
    o += text(1246, 474, "The one it cannot fix", size=20, weight="700", anchor="start")
    for i, ln in enumerate(["A correctly signed image that",
                            "installs, boots, then crashes.",
                            "The old firmware is gone and",
                            "the update menu lived inside",
                            "the app — so nothing can",
                            "recover it but a probe."]):
        o += text(1200, 512 + i * 24, ln, size=16, fill=INK_SOFT, anchor="start")

    o += rect(96, 786, 1036, 64, fill=GRAY_LT, stroke=GRAY_BD, rx=14, sw=2)
    o += text(120, 826, "Forged, corrupted or out-of-date images are rejected at step 4 — before anything is overwritten.",
              size=19, anchor="start")
    return write("05-overwrite-sequence", o)


# =============================================================== diagram 6 ===
def d06_swap():
    o = title_block("Dual slot, SWAP — the device rescues itself",
                    "The old firmware is kept. The new one must prove it works, or it is put back automatically.")
    y = 182
    for n, cap, s1, s2, tag in [
            (1, "Download and request, exactly as before", "run", "staged", "MAGIC"),
            (2, "Reset — the RoT verifies, then EXCHANGES the two slots", "new", "old", None)]:
        o += step_dot(96, y + 40, n, color=INK)
        o += text(132, y + 16, cap, size=20, weight="700", anchor="start")
        o += slot_pair(132, y + 30, 1360, 74, s1, s2, tag2=tag)
        y += 122

    o += step_dot(96, y + 30, 3, color=INK)
    o += text(132, y + 6, "The new firmware runs — on trial", size=20, weight="700", anchor="start")
    o += rect(132, y + 22, 1360, 56, fill=AMBER_LT, stroke=AMBER, rx=10, sw=2.4)
    o += text(812, y + 56, "it must write the confirmation flag at 0x8BFE0  —  \"I booted, keep me\"",
              size=19, fill=INK, weight="600")

    yb = y + 118
    o += line(812, yb, 812, yb + 26, color=INK, sw=2.6)
    o += path(f"M812,{yb+26} L432,{yb+26} L432,{yb+58}", stroke=INK, sw=2.6, marker="arInk")
    o += path(f"M812,{yb+26} L1192,{yb+26} L1192,{yb+58}", stroke=INK, sw=2.6, marker="arInk")

    ybox = yb + 62
    o += card(132, ybox, 600, 210, fill=GREEN_LT, stroke=GREEN, sw=2.6)
    o += check(180, ybox + 40, GREEN, 1.2)
    o += text(210, ybox + 48, "Confirmed", size=23, weight="700", anchor="start")
    o += text(432, ybox + 84, "the flag was written", size=17, fill=INK_SOFT)
    o += slot_pair(162, ybox + 104, 540, 62, "run", "old", "PRIMARY", "SECONDARY")
    o += text(432, ybox + 192, "the update sticks", size=17, fill=GREEN, weight="700")

    o += card(892, ybox, 600, 210, fill=RED_LT, stroke=RED, sw=2.6)
    o += cross(940, ybox + 40, RED, 1.1)
    o += text(970, ybox + 48, "Not confirmed", size=23, weight="700", anchor="start")
    o += text(1192, ybox + 84, "crash · hang · watchdog · power loss", size=17, fill=INK_SOFT)
    o += slot_pair(922, ybox + 104, 540, 62, "run", "old", "PRIMARY", "SECONDARY",
                   note1="PREVIOUS, restored", note2="the failed one")
    o += text(1192, ybox + 192, "the RoT swaps back by itself — no probe, no truck roll",
              size=17, fill=RED, weight="700")
    return write("06-swap-sequence", o)


# =============================================================== diagram 7 ===
def d07_bank_swap():
    o = title_block("Bank swap (mirror) — move the map, not the firmware",
                    "One option-byte write instead of copying 464 KB. Install time drops to almost nothing.")
    def bank_stack(x, y, top_name, top_state, bot_name, bot_state, label, addr=True):
        s = text(x + 190, y - 22, label, size=20, weight="700")
        s += slot(x, y, 380, 108, top_state, top_name)
        s += slot(x, y + 122, 380, 108, bot_state, bot_name)
        if addr:
            s += text(x - 14, y + 54, "0x08000000", size=15, fill=INK_SOFT,
                      anchor="end", family=MONO)
            s += text(x - 14, y + 176, "0x08080000", size=15, fill=INK_SOFT,
                      anchor="end", family=MONO)
        return s

    o += bank_stack(240, 250, "BANK 1", "run", "BANK 2", "new", "SWAP_BANK = 0")
    o += bank_stack(980, 250, "BANK 2", "run", "BANK 1", "old", "SWAP_BANK = 1",
                    addr=False)

    o += path("M640,364 C750,364 800,304 968,304", stroke=VIOLET, sw=3.4, marker="arCyan")
    o += path("M640,436 C750,436 800,426 968,426", stroke=VIOLET, sw=3.4, marker="arCyan")
    o += rect(650, 372, 220, 56, fill=VIOLET, rx=14)
    o += text(760, 398, "write one option byte", size=16, fill=WHITE, weight="700")
    o += text(760, 419, "+ reset", size=16, fill=WHITE, weight="700")

    o += card(240, 542, 560, 150, fill=GREEN_LT, stroke=GREEN, sw=2.4)
    o += check(286, 584, GREEN, 1.1)
    o += text(312, 592, "What you gain", size=21, weight="700", anchor="start")
    for i, ln in enumerate(["install time ≈ 0 — nothing is copied",
                            "revert is another flip, just as fast",
                            "flash wear drops to almost nothing"]):
        o += text(276, 626 + i * 26, "•  " + ln, size=17, fill=INK_SOFT, anchor="start")

    o += card(840, 542, 700, 150, fill=RED_LT, stroke=RED, sw=2.4)
    o += cross(886, 584, RED, 1.0)
    o += text(912, 592, "The catch you must solve first", size=21, weight="700", anchor="start")
    for i, ln in enumerate(["SWAP_BANK exchanges the WHOLE map — including 0x08000000,",
                            "where the immutable RoT itself lives. The bootloader moves too.",
                            "Usual answer: an identical, write-protected copy in both banks."]):
        o += text(876, 626 + i * 26, ln, size=16, fill=INK_SOFT, anchor="start")

    o += rect(240, 722, 1300, 60, fill=AMBER_LT, stroke=AMBER, rx=14, sw=2.4)
    o += text(890, 760, "Status: not implemented in this repository — SWAP_BANK exists only as an option byte set to 0.",
              size=19, weight="700")
    return write("07-bank-swap", o)


# =============================================================== diagram 8 ===
def d08_variants():
    o = title_block("Four ways to arrange the flash",
                    "Same bootloader (navy), same cryptography — only the slot strategy changes")
    cards = [
        ("SINGLE SLOT", "no field update",
         [("RoT", 96, INK), ("APPLICATION", 928, GREEN)],
         "~925 KB for the app", "a probe is the only way in", RED),
        ("DUAL — OVERWRITE", "runs today",
         [("RoT", 96, INK), ("PRIMARY", 464, GREEN), ("SECONDARY", 464, CYAN_DK)],
         "~464 KB for the app", "no way back from a bad image", AMBER),
        ("DUAL — SWAP", "auto-revert",
         [("RoT", 96, INK), ("PRIMARY", 464, GREEN), ("SECONDARY", 464, CYAN_DK)],
         "~460 KB for the app", "the old image is preserved", GREEN),
        ("EXTERNAL DOWNLOAD", "big app",
         [("RoT", 96, INK), ("APPLICATION", 928, GREEN)],
         "~925 KB for the app", "secondary slot lives on QSPI", GREEN),
    ]
    x = 64
    for name, tagline, segs, budget, note, notecol in cards:
        cw = 356
        o += card(x, 180, cw, 470, fill=WHITE, stroke=GRAY_BD, sw=2.4)
        o += rect(x, 180, cw, 6, fill=notecol, rx=3)
        o += text(x + cw / 2, 226, name, size=21, weight="700")
        o += text(x + cw / 2, 252, tagline, size=16, fill=notecol, weight="700")
        total = sum(s[1] for s in segs)
        bar_w = cw - 56
        xx = x + 28
        for sname, kb_, col in segs:
            w = bar_w * kb_ / total
            o += rect(xx, 280, w, 62, fill=col, rx=6)
            if w > 70:
                o += text(xx + w / 2, 318, sname, size=14, fill=WHITE, weight="700")
            xx += w
        if name == "EXTERNAL DOWNLOAD":
            o += rect(x + 28, 362, bar_w, 54, fill=CYAN_LT, stroke=CYAN_DK, rx=8, sw=2.2, dash="7 5")
            o += text(x + cw / 2, 386, "QSPI — SECONDARY", size=15, fill=CYAN_DK, weight="700")
            o += text(x + cw / 2, 406, "external component", size=13, fill=INK_SOFT)
        o += text(x + cw / 2, 458, budget, size=19, weight="700")
        o += text(x + cw / 2, 496, note, size=16, fill=INK_SOFT)

        icons = [("auto-revert", name in ("DUAL — SWAP",)),
                 ("field update", name != "SINGLE SLOT"),
                 ("no extra hardware", name != "EXTERNAL DOWNLOAD")]
        for i, (lbl, ok) in enumerate(icons):
            yy = 540 + i * 36
            if ok:
                o += check(x + 44, yy, GREEN, 0.85)
            else:
                o += cross(x + 44, yy, RED, 0.8)
            o += text(x + 68, yy + 7, lbl, size=16, fill=INK_SOFT, anchor="start")
        x += cw + 32

    o += rect(64, 690, 1472, 150, fill=GRAY_LT, stroke=GRAY_BD, rx=16, sw=2)
    o += text(90, 730, "The question that picks the column:", size=22, weight="700", anchor="start")
    o += text(90, 774, "\"If a correctly signed firmware installs, boots, and then fails — who rescues the device?\"",
              size=21, fill=INK, anchor="start")
    o += text(90, 812, "The bootloader (swap) · a human with a probe (overwrite, single slot) · nobody (a locked device).",
              size=18, fill=INK_SOFT, anchor="start")
    return write("08-architecture-variants", o)


# =============================================================== diagram 9 ===
def d09_comparison():
    o = title_block("Side by side",
                    "Green is where a choice costs you nothing — amber and red are where it bites")
    cols = ["Single slot", "Overwrite", "Swap", "Bank swap", "External"]
    rows = [
        ("Application budget", ["~925 KB", "~464 KB", "~460 KB", "~460 KB", "~925 KB"],
         [GREEN, AMBER, AMBER, AMBER, GREEN]),
        ("Install time", ["n/a", "one copy", "two copies", "instant", "copy + QSPI"],
         [INK_SOFT, GREEN, AMBER, GREEN, AMBER]),
        ("Old firmware kept", ["no", "no", "yes", "yes", "no"],
         [RED, RED, GREEN, GREEN, RED]),
        ("Auto-revert on crash", ["no", "no", "yes", "yes", "no"],
         [RED, RED, GREEN, GREEN, RED]),
        ("App must confirm", ["no", "no", "yes", "yes", "no"],
         [GREEN, GREEN, AMBER, AMBER, GREEN]),
        ("Power-fail safe install", ["no", "yes", "yes", "yes", "yes"],
         [RED, GREEN, GREEN, GREEN, GREEN]),
        ("Extra hardware", ["no", "no", "no", "no", "QSPI chip"],
         [GREEN, GREEN, GREEN, GREEN, AMBER]),
        ("Status in this repo", ["not built", "WORKS TODAY", "app side ready", "not implemented", "driver only"],
         [INK_SOFT, GREEN, AMBER, RED, AMBER]),
    ]
    x0, y0, lw, cw, rh = 64, 210, 380, 222, 72
    for j, c in enumerate(cols):
        xx = x0 + lw + j * cw
        hl = (c == "Overwrite")
        o += rect(xx, y0 - 56, cw - 10, 50, fill=INK if hl else GRAY_LT,
                  stroke=None if hl else GRAY_BD, rx=10, sw=1.6)
        o += text(xx + (cw - 10) / 2, y0 - 22, c, size=19,
                  fill=WHITE if hl else INK, weight="700")
    for i, (label, vals, colors) in enumerate(rows):
        yy = y0 + i * rh
        if i % 2 == 0:
            o += rect(x0, yy, lw + len(cols) * cw - 10, rh - 8, fill=GRAY_LT, rx=8)
        o += text(x0 + 18, yy + 44, label, size=19, weight="600", anchor="start")
        for j, v in enumerate(vals):
            xx = x0 + lw + j * cw
            col = colors[j]
            bg = {GREEN: GREEN_LT, AMBER: AMBER_LT, RED: RED_LT}.get(col, WHITE)
            o += rect(xx + 8, yy + 10, cw - 26, rh - 28, fill=bg, stroke=col, rx=9, sw=1.8)
            o += text(xx + (cw - 10) / 2, yy + 44, v, size=17, fill=col, weight="700")
    o += text(64, 840, "\"Works today\" is the column the board boots from right now. Everything else is a decision, not a fact.",
              size=19, fill=INK_SOFT, anchor="start")
    return write("09-comparison", o)


# ============================================================== diagram 10 ===
def d10_failure_modes():
    o = title_block("What happens when an update goes wrong",
                    "Four of the five failures are handled identically — the fifth is the whole argument")
    rows = [
        ("Forged or re-signed with the wrong key", "rejected before install", "rejected before install", True, True),
        ("Corrupted during the transfer", "hash mismatch — rejected", "hash mismatch — rejected", True, True),
        ("Genuine, but an old vulnerable version", "below the counter — rejected", "below the counter — rejected", True, True),
        ("Power lost during the install", "the copy restarts", "the swap resumes", True, True),
        ("Correctly signed — but it crashes at runtime", "device stuck — needs a probe", "reverts by itself, next boot", False, True),
    ]
    x0, y0, lw, cw, rh = 64, 250, 620, 440, 104
    for j, (c, hl) in enumerate([("OVERWRITE", True), ("SWAP / BANK SWAP", False)]):
        xx = x0 + lw + j * cw
        o += rect(xx, y0 - 58, cw - 16, 48, fill=INK if hl else CYAN_DK, rx=10)
        o += text(xx + (cw - 16) / 2, y0 - 25, c, size=19, fill=WHITE, weight="700")
    for i, (label, a, b, oka, okb) in enumerate(rows):
        yy = y0 + i * rh
        last = (i == len(rows) - 1)
        if last:
            o += rect(x0 - 10, yy - 6, lw + 2 * cw + 10, rh - 4, fill=AMBER_LT,
                      stroke=AMBER, rx=12, sw=2.4)
        elif i % 2 == 0:
            o += rect(x0, yy, lw + 2 * cw - 16, rh - 12, fill=GRAY_LT, rx=8)
        o += text(x0 + 18, yy + 52, label, size=19,
                  weight="700" if last else "600", anchor="start")
        for j, (v, ok) in enumerate(((a, oka), (b, okb))):
            xx = x0 + lw + j * cw
            col = GREEN if ok else RED
            bg = GREEN_LT if ok else RED_LT
            o += rect(xx + 8, yy + 12, cw - 40, rh - 36, fill=bg, stroke=col, rx=10, sw=2)
            if ok:
                o += check(xx + 42, yy + 46, col, 1.0)
            else:
                o += cross(xx + 42, yy + 46, col, 0.95)
            o += text(xx + 70, yy + 53, v, size=17, fill=col, weight="700", anchor="start")
    o += rect(64, 800, 1472, 62, fill=INK, rx=14)
    o += text(800, 840, "Signatures stop bad firmware. Only a second slot stops bad-but-genuine firmware.",
              size=22, fill=WHITE, weight="700")
    return write("10-failure-modes", o)


# ============================================================== diagram 11 ===
def d11_trust_model():
    o = title_block("How the device knows the firmware is yours",
                    "Signing proves who made it · encryption stops anyone reading it · they are independent choices")
    # image anatomy
    o += text(64, 182, "What an image actually is", size=22, weight="700", anchor="start")
    segs = [("HEADER", 200, VIOLET, "0x400"), ("ENCRYPTED PAYLOAD", 780, CYAN_DK, "your firmware"),
            ("TLVs", 420, GREEN, "hash · signature · version · dependencies")]
    x = 64
    for name, w, col, sub in segs:
        o += rect(x, 200, w - 10, 92, fill=col, rx=10)
        o += text(x + (w - 10) / 2, 240, name, size=19, fill=WHITE, weight="700")
        o += text(x + (w - 10) / 2, 266, sub, size=15, fill=WHITE, opacity=0.85)
        x += w

    # factory vs device
    o += card(64, 344, 700, 300, fill=VIOLET_LT, stroke=VIOLET, sw=2.4, title="IN THE FACTORY  (offline)")
    o += text(414, 404, "signing PRIVATE key", size=20, weight="700", fill=VIOLET)
    o += text(414, 434, "never leaves — if it leaks, every device is lost", size=16, fill=INK_SOFT)
    o += rect(120, 458, 588, 2, fill=VIOLET, opacity=0.35)
    o += text(414, 496, "encryption key (ECIES P-256)", size=20, weight="700", fill=VIOLET)
    o += text(414, 526, "scrambles the payload with AES-128", size=16, fill=INK_SOFT)
    o += text(414, 590, "one key pair today — no revocation path", size=17, fill=RED, weight="700")
    o += text(414, 616, "and the bootloader is immutable, so it cannot be added later",
              size=15, fill=RED, opacity=0.85)

    o += card(836, 344, 700, 300, fill=GREEN_LT, stroke=GREEN, sw=2.4, title="ON THE DEVICE  (0x12000, hidden by HDP)")
    o += text(1186, 404, "SHA-256 of the public key   (32 bytes)", size=20, weight="700", fill=GREEN)
    o += text(1186, 434, "not the key itself — the image carries that, and the hash proves it",
              size=16, fill=INK_SOFT)
    o += rect(892, 458, 588, 2, fill=GREEN, opacity=0.35)
    o += text(1186, 496, "decryption key — raw in flash", size=20, weight="700", fill=AMBER)
    o += text(1186, 526, "readable by anyone who defeats RDP and HDP", size=16, fill=INK_SOFT)
    o += text(1186, 590, "stronger option: keep it inside SAES hardware", size=17, fill=AMBER, weight="700")
    o += text(1186, 616, "so the usable key never exists in readable memory", size=15, fill=INK_SOFT)

    o += path("M764,470 C790,470 810,470 830,470", stroke=INK, sw=3, marker="arInk")

    o += rect(64, 686, 1472, 156, fill=WHITE, stroke=GRAY_BD, rx=16, sw=2)
    o += text(90, 726, "Two questions people mix up:", size=21, weight="700", anchor="start")
    o += check(112, 764, GREEN, 0.95)
    o += text(140, 771, "\"Is this firmware really from us?\"  →  SIGNING. Without it, anyone can install anything.",
              size=19, anchor="start")
    o += check(112, 810, GREEN, 0.95)
    o += text(140, 817, "\"Can a competitor read our firmware?\"  →  ENCRYPTION. Optional — drop it and one key leaves the device.",
              size=19, anchor="start")
    return write("11-trust-model", o)


# ============================================================== diagram 12 ===
def d12_decision_tree():
    o = title_block("Six questions, in this order",
                    "Each answer removes whole branches — the last two cannot be changed after production")
    qs = [
        ("1", "Is the firmware updated in the field at all?",
         "no → single slot, and most of this is moot", GREEN),
        ("2", "If a signed firmware boots and then fails, must the device recover by itself?",
         "yes → swap   ·   no → overwrite", GREEN),
        ("3", "Does the application fit in ~464 KB?",
         "no → external download slot, or revisit question 2", GREEN),
        ("4", "Is the firmware confidential?",
         "no → drop encryption   ·   yes → raw key or SAES-held key", CYAN_DK),
        ("5", "What happens if the signing key leaks?",
         "\"we accept losing the fleet\" — or design revocation NOW", RED),
        ("6", "What is the production lock-down?",
         "RDP level · tamper policy · dev mode off · regression allowed or not", RED),
    ]
    y = 178
    for n, q, a, col in qs:
        o += rect(64, y, 1030, 92, fill=WHITE, stroke=col, rx=14, sw=2.4)
        o += step_dot(112, y + 46, n, color=col, r=22)
        o += text(154, y + 40, q, size=21, weight="700", anchor="start")
        o += text(154, y + 68, a, size=17, fill=INK_SOFT, anchor="start")
        if n in ("5", "6"):
            o += rect(886, y + 24, 186, 44, fill=RED, rx=22)
            o += text(979, y + 53, "IRREVERSIBLE", size=16, fill=WHITE, weight="700")
        y += 106

    o += card(1104, 178, 432, 316, fill=GRAY_LT, stroke=GRAY_BD, sw=2.4,
              title="Where the answers land")
    profiles = [("P0", "Lab — ships today", INK), ("P1", "No field update", INK_SOFT),
                ("P2", "Production overwrite", GREEN), ("P3", "Safe update (swap)", GREEN),
                ("P4", "Big app (external)", CYAN_DK), ("P5", "High assurance", VIOLET)]
    for i, (p, d, col) in enumerate(profiles):
        yy = 230 + i * 42
        o += rect(1130, yy, 60, 32, fill=col, rx=8)
        o += text(1160, yy + 23, p, size=17, fill=WHITE, weight="700")
        o += text(1204, yy + 23, d, size=17, anchor="start")

    o += rect(1104, 516, 432, 236, fill=RED_LT, stroke=RED, rx=16, sw=2.4)
    o += text(1320, 560, "Decide 5 and 6 first", size=21, weight="700")
    for i, ln in enumerate(["They are listed last because the",
                            "earlier answers shape them —",
                            "but they must be settled before",
                            "the first device is provisioned.",
                            "After that, the bootloader and the",
                            "option bytes are locked forever."]):
        o += text(1320, 600 + i * 25, ln, size=16, fill=INK_SOFT)

    o += rect(64, 814, 1030, 48, fill=INK, rx=12)
    o += text(579, 846, "Questions 1–4 are engineering. Questions 5–6 are commitments.",
              size=20, fill=WHITE, weight="700")
    return write("12-decision-tree", o)


# ============================================================== diagram 13 ===
def _qa(x, y, w, q, a, bullets, col, colbg, qh=54):
    """One question/answer block."""
    o = rect(x, y, w, qh, fill=col, rx=12)
    o += text(x + 26, y + qh / 2 + 8, q, size=22, fill=WHITE, weight="700", anchor="start")
    o += text(x + 26, y + qh + 44, a, size=21, fill=col, weight="700", anchor="start")
    for i, b in enumerate(bullets):
        o += text(x + 26, y + qh + 80 + i * 28, "•  " + b, size=17,
                  fill=INK_SOFT, anchor="start")
    return o


def d13_faq_images():
    o = title_block("Questions that keep coming up  (1/2)",
                    "The image format, and what the application is allowed to touch")

    o += _qa(64, 168, 1472,
             "What is the \"magic trailer\"?",
             "A 16-byte flag the app writes at the very end of the download slot — \"a candidate is ready\".",
             ["MCUboot's standard value, written at 0xFFFF0 in one flash programming unit (0x10 bytes)",
              "It sits AFTER the image data, so it can only be complete if the whole download was — power loss leaves no magic, and the RoT ignores the slot",
              "It is not a trust signal: the app writes it, so a forged one only makes the RoT verify and reject"],
             INK, WHITE)

    o += rect(64, 382, 1472, 74, fill=GRAY_LT, stroke=GRAY_BD, rx=12, sw=2)
    o += text(96, 412, "secondary slot", size=16, fill=INK_SOFT, anchor="start")
    o += text(96, 438, "0x8C000", size=15, fill=INK_SOFT, anchor="start", family=MONO)
    o += rect(300, 394, 1140, 50, fill=CYAN_LT, stroke=CYAN_DK, rx=8, sw=2)
    o += text(830, 425, "image data, written front to back", size=18, fill=CYAN_DK, weight="600")
    o += rect(1448, 394, 76, 50, fill=VIOLET, rx=8)
    o += text(1486, 418, "MAGIC", size=13, fill=WHITE, weight="700")
    o += text(1486, 436, "16 B", size=12, fill=WHITE, opacity=0.85)
    o += text(1486, 470, "0xFFFF0", size=15, fill=VIOLET, weight="700", family=MONO)

    o += _qa(64, 512, 1472,
             "The image arrives encrypted — should the app decrypt it before writing to flash?",
             "No. Write it byte for byte, still encrypted. The application never decrypts anything.",
             ["It could not anyway: the decryption key is at 0x12000, inside HDP, which closes before the app runs",
              "The RoT unwraps the AES key, decrypts on the fly while hashing (the signature covers the PLAINTEXT), then decrypts while installing",
              "Invariant: primary slot = clear, secondary slot = encrypted — visible in the two image recipes (-c vs -E)",
              "In swap mode the RoT re-encrypts the outgoing image on its way to the secondary slot"],
             GREEN, WHITE)

    o += rect(64, 816, 1472, 56, fill=INK, rx=12)
    o += text(800, 852, "All the security is in the image format, not in the pipe — so the transport can be anything.",
              size=20, fill=WHITE, weight="700")
    return write("13-faq-images", o)


# ============================================================== diagram 14 ===
def d14_faq_data():
    o = title_block("Questions that keep coming up  (2/2)",
                    "Configuration and calibration data, and why it must live outside the slots")

    o += _qa(64, 168, 1472,
             "We keep calibration and configuration in flash. Must we mirror it into both slots?",
             "No — move it OUT of the slots. The bootloader never touches anything outside them.",
             ["Inside a slot it does not survive: overwrite erases the primary slot wholesale;",
              "swap carries the page out to the secondary slot, hands back a sector of the incoming image — and a revert undoes it again",
              "Mirroring inside the slots does not help; a dedicated region outside them does"],
             VIOLET, WHITE)

    # before / after strips -------------------------------------------------
    x0, wtot = 64, 1472

    y = 430
    o += cross(84, y - 20, RED, 0.8)
    o += text(108, y - 13, "today — the slots run to the top of flash, nothing is reserved",
              size=18, weight="700", anchor="start")
    kb = wtot / 1024.0
    for name, off, size_kb, col in (("RoT + keys", 0, 96, INK),
                                    ("PRIMARY  464 KB", 96, 464, GREEN),
                                    ("SECONDARY  464 KB", 560, 464, CYAN_DK)):
        o += rect(x0 + off * kb, y, size_kb * kb - 4, 54, fill=col, rx=7)
        o += text(x0 + (off + size_kb / 2) * kb, y + 34, name, size=18,
                  fill=WHITE, weight="700")

    y2 = 566
    o += check(84, y2 - 20, GREEN, 0.8)
    o += text(108, y2 - 13,
              "one way to make room — 16 KB reserved, taken from both slots   (data block not to scale)",
              size=18, weight="700", anchor="start")
    dataw = 124
    kb2 = (wtot - dataw) / 1008.0
    xx = x0
    for name, size_kb, col in (("RoT + keys", 96, INK),
                               ("PRIMARY  456 KB", 456, GREEN),
                               ("SECONDARY  456 KB", 456, CYAN_DK)):
        w = size_kb * kb2
        o += rect(xx, y2, w - 4, 54, fill=col, rx=7)
        o += text(xx + w / 2, y2 + 34, name, size=18, fill=WHITE, weight="700")
        if name != "RoT + keys":
            o += text(xx, y2 + 82, "0x18000" if "PRIMARY" in name else "0x8A000",
                      size=15, fill=INK_SOFT, anchor="start", family=MONO)
        xx += w
    o += rect(xx, y2, dataw, 54, fill=VIOLET, rx=7)
    o += text(xx + dataw / 2, y2 + 26, "DATA", size=17, fill=WHITE, weight="700")
    o += text(xx + dataw / 2, y2 + 46, "16 KB", size=14, fill=WHITE, opacity=0.9)
    o += text(xx, y2 + 82, "0xFC000", size=15, fill=VIOLET, weight="700",
              anchor="start", family=MONO)

    cards = [("Swap needs equal slots", RED,
              ["so N bytes of data area", "costs 2N bytes of flash"]),
             ("Do not rewrite a struct in place", AMBER,
              ["copy boot_nv_counters.c:", "append + CRC, newest wins"]),
             ("Signed data shipped by you", GREEN,
              ["is a different mechanism —", "the data image (2 more slots)"])]
    x = 64
    for t, col, lines in cards:
        o += rect(x, 706, 476, 112, fill=WHITE, stroke=col, rx=14, sw=2.4)
        o += text(x + 24, 740, t, size=19, fill=col, weight="700", anchor="start")
        for i, ln in enumerate(lines):
            o += text(x + 24, 770 + i * 25, ln, size=16, fill=INK_SOFT, anchor="start")
        x += 504

    o += text(64, 862, "Also: the primary slot spills 48 KB past the 0x80000 bank boundary — so \"put the data in the other bank\" needs a re-layout first.",
              size=18, fill=INK_SOFT, anchor="start")
    return write("14-faq-data", o)


# ------------------------------------------------------------------- main ---
DIAGRAMS = [d01_two_stage_boot, d02_flash_map, d03_pipeline, d04_boot_decision,
            d05_overwrite, d06_swap, d07_bank_swap, d08_variants, d09_comparison,
            d10_failure_modes, d11_trust_model, d12_decision_tree,
            d13_faq_images, d14_faq_data]


def main():
    made = [fn() for fn in DIAGRAMS]
    print(f"{len(made)} SVG files -> {SVG_DIR}")
    if "--no-png" in sys.argv:
        return
    try:
        import cairosvg
    except ImportError:
        print("cairosvg not installed - skipping PNG export (pip install cairosvg)")
        return
    os.makedirs(PNG_DIR, exist_ok=True)
    for p in made:
        out = os.path.join(PNG_DIR, os.path.basename(p)[:-4] + ".png")
        cairosvg.svg2png(url=p, write_to=out, scale=2.0,
                         background_color="white")
    print(f"{len(made)} PNG files  -> {PNG_DIR}")


if __name__ == "__main__":
    main()
