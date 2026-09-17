# Presentation diagrams

Slide-ready versions of the schemes in [`../../DOC.md`](../../DOC.md),
[`../../ARCHITECTURE_CHOICES.md`](../../ARCHITECTURE_CHOICES.md) and
[`../../UPDATE_FLOWS.md`](../../UPDATE_FLOWS.md).

| | |
|---|---|
| `svg/` | vector, 1600 × 900, **transparent background** — the format to use in PowerPoint |
| `png/` | 3200 × 1800 on white — fallback for templates or tools that dislike SVG |
| `oemirot_architecture.pptx` | 16:9 deck, one diagram per slide, with speaker notes |
| `generate_diagrams.py` | regenerates everything in `svg/` and `png/` |
| `build_pptx.py` | rebuilds the deck from `png/` |

## The twelve diagrams

| # | File | Shows |
|---|---|---|
| 01 | `01-two-stage-boot` | the two stages and the one-way jump |
| 02 | `02-flash-map` | the real 1 MB layout, with WRP/HDP spans |
| 03 | `03-update-pipeline` | factory → transport → device, and who does what |
| 04 | `04-boot-decision` | what the RoT does on every reset, with the rejection paths |
| 05 | `05-overwrite-sequence` | dual-slot overwrite, step by step (what runs today) |
| 06 | `06-swap-sequence` | dual-slot swap, with the confirm / auto-revert branch |
| 07 | `07-bank-swap` | the `SWAP_BANK` mirror idea, and its open question |
| 08 | `08-architecture-variants` | the four slot arrangements side by side |
| 09 | `09-comparison` | full trade-off matrix, including status in this repo |
| 10 | `10-failure-modes` | what happens to a bad image, overwrite vs. swap |
| 11 | `11-trust-model` | signing vs. encryption, and where each key lives |
| 12 | `12-decision-tree` | the six questions, in the order to answer them |

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
python3 build_pptx.py                 # oemirot_architecture.pptx
```

Colours, fonts and the slot-state vocabulary live at the top of `generate_diagrams.py`;
change the palette constants there to match a corporate template and re-run.

## Accuracy

Offsets, sizes and flag names come from `NUCLEO-C5A3ZG/oemirot/flash_layout.h`,
`mcuboot_config.h` and `NUCLEO-C5A3ZG/appli/appli_flash_layout.h`. Diagrams 07 and parts
of 08–09 describe arrangements that are **not implemented in this repository** and say so
on the slide itself — keep those labels if you reuse the slides.
