# Presentation diagrams

Slide-ready versions of the schemes in [`../../DOC.md`](../../DOC.md),
[`../../ARCHITECTURE_CHOICES.md`](../../ARCHITECTURE_CHOICES.md) and
[`../../UPDATE_FLOWS.md`](../../UPDATE_FLOWS.md).

| | |
|---|---|
| `svg/` | vector, 1600 × 900, **transparent background** — the format to use in PowerPoint |
| `png/` | 3200 × 1800 on white — fallback for templates or tools that dislike SVG |
| `oemirot_architecture.pptx` | **16:9 deck built from native PowerPoint shapes — every box, line and label is editable.** With speaker notes |
| `oemirot_architecture_images.pptx` | the same deck with each slide as a flat picture — pixel-exact, not editable |
| `generate_diagrams.py` | regenerates everything in `svg/` and `png/` |
| `build_pptx_editable.py` | rebuilds the editable deck (native shapes, no pictures) |
| `build_pptx.py` | rebuilds the picture deck from `png/` |

## The twenty diagrams

| # | File | Shows |
|---|---|---|
| 00 | `00-glossary` | every term the deck uses — RoT, TLV, HDP, WRP, RDP, MPU, NV counter, ECIES, XIP… |
| 01 | `01-two-stage-boot` | the two stages and the one-way jump |
| 02 | `02-flash-map` | the real 1 MB layout, with WRP/HDP spans |
| 03 | `03-update-pipeline` | factory → transport → device, and who does what |
| 04 | `04-boot-decision` | what the RoT does on every reset, with the rejection paths |
| 05 | `05-overwrite-sequence` | dual-slot overwrite, step by step (what runs today) |
| 05b | `05b-why-install-request` | why the app must explicitly ask for installation, not just download |
| 06 | `06-swap-sequence` | dual-slot swap, with the confirm / auto-revert branch |
| 07b | `07b-bank-swap-cost` | what bank swap would force you to mirror, and the flash it costs |
| 07 | `07-bank-swap` | the `SWAP_BANK` mirror idea, and its open question |
| 08 | `08-architecture-variants` | the four slot arrangements side by side |
| 09 | `09-comparison` | full trade-off matrix, including status in this repo |
| 10 | `10-failure-modes` | what happens to a bad image, overwrite vs. swap |
| 11b | `11b-decryption-timeline` | at which stage the image is decrypted — twice, both inside the bootloader |
| 11 | `11-trust-model` | signing vs. encryption, and where each key lives |
| 12 | `12-decision-tree` | the six questions, in the order to answer them |
| 13 | `13-faq-images` | FAQ — the magic trailer, and why the app writes the image still encrypted |
| 14 | `14-faq-data` | FAQ — where calibration and configuration data must live |
| 15 | `15-faq-swap-and-speed` | FAQ — swap needs one bootloader, and encryption costs no runtime |
| 16 | `16-open-questions` | the questions this analysis cannot answer — for the team to own |

## Which deck to use

**`oemirot_architecture.pptx` is the one to edit.** Every rectangle, arrow, circle and
label is a real PowerPoint object: click it, drag it, recolour it, retype it. No
"convert to shape" step, no pictures. It is also ~25× smaller than the picture deck.

Two things to know before you edit:

- **Labels are separate text boxes**, not text inside their rectangle. Moving a box does
  not carry its label — select both (or rubber-band the group) when repositioning.
- **Fonts decide the layout.** Text is Segoe UI (Consolas for addresses). On a machine
  without Segoe UI, PowerPoint substitutes and a long label may sit a pixel or two off.
  Nudge it, or use the picture deck where exactness matters.

`oemirot_architecture_images.pptx` keeps each slide as a rendered picture — identical to
the SVGs down to the pixel, useful for printing or for handing to someone who should not
be changing the content.

## Using them in PowerPoint

- **SVG** — Insert ▸ Pictures ▸ pick the `.svg`. To recolour it for your template,
  right-click ▸ *Convert to Shape*; every box and label becomes editable.
  Text uses Segoe UI with Arial as fallback, so it renders on any Windows or Mac machine.
- **PNG** — already on a white background, drop-in anywhere.
- Diagrams are drawn at 1600 × 900, so they fill a 16:9 slide exactly with no cropping.
- The SVGs have no background of their own: they sit on light slide masters as they are.
  On a dark master, use the PNGs or set a light panel behind the picture.

## Regenerating

```bash
pip install cairosvg python-pptx      # only needed for the PNG and PPTX steps
python3 generate_diagrams.py          # svg/ + png/   (--no-png to skip the raster export)
python3 build_pptx_editable.py        # oemirot_architecture.pptx         (native shapes)
python3 build_pptx.py                 # oemirot_architecture_images.pptx  (pictures)
```

`build_pptx_editable.py` replays the *same* drawing calls the SVG generator uses —
`generate_diagrams.py` exposes a "rec" mode that records primitives instead of emitting
SVG — so the two decks can never drift apart. Adding a diagram to `DIAGRAMS` and to the
`SLIDES` list in `build_pptx.py` updates both.

Colours, fonts and the slot-state vocabulary live at the top of `generate_diagrams.py`;
change the palette constants there to match a corporate template and re-run.

## Accuracy

Offsets, sizes and flag names come from `NUCLEO-C5A3ZG/oemirot/flash_layout.h`,
`mcuboot_config.h` and `NUCLEO-C5A3ZG/appli/appli_flash_layout.h`. Diagram 07 and parts
of 08–09 describe arrangements that are **not implemented in this repository** and say so
on the slide itself — keep those labels if you reuse the slides.
