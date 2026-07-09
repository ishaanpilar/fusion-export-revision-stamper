# Export Revision Stamper

A small Fusion 360 add-in that stamps the design's current revision onto
exported STEP/STL/3MF filenames, so a filename never lies about what
revision it is — and keeps a local log of every export as a handoff record.

It is deliberately not a PDM system. It solves one problem: the exported
file someone sends to a vendor should always be labeled with the right
revision, and there should be a record of it.

## Why

Fusion tracks an internal version number (`v7`) but won't export it as a
`Rev` tag, and the version isn't part of the exported filename unless you
type it in by hand. That leads to manually-typed filenames like
`bracket_final_v2_REAL.step` — and to vendors occasionally cutting the wrong
revision.

## What it does

1. Adds an **"Export w/ Revision Stamp"** command to the Utilities tab
   (`SolidScriptsAddinsPanel`).
2. On export, builds the filename from a configurable template using the
   document's actual saved version number (`design.dataFile.versionNumber`),
   converted to a revision letter (`1 -> A`, `26 -> Z`, `27 -> AA`, ...).
3. Warns you before exporting if the document has unsaved changes newer than
   its last saved revision — so the stamp doesn't lie.
4. Appends a row to `handoff_log.csv` in the output folder: timestamp, part
   name, version, revision, format, filename, and an optional vendor/note
   field you type in per export.

## Filename template

Default: `{name}_Rev{revletter}_{date}.{ext}`

Available fields:

| Field         | Example                                        |
|---------------|------------------------------------------------|
| `{name}`      | `bracket`                                      |
| `{version}`   | `7`                                            |
| `{revletter}` | `G`                                            |
| `{rev}`       | `7` (alias of `{version}`)                     |
| `{date}`      | `20260709`                                     |
| `{ext}`       | `step`                                         |
| `{note}`      | whatever you type in the "Vendor / Note" field |

The template and last-used output folder are remembered in `settings.json`
next to the add-in (created on first run).

## Install

1. Copy the `ExportRevisionStamper` folder into Fusion's add-ins directory:
   - macOS: `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/`
   - Windows: `%appdata%\Autodesk\Autodesk Fusion 360\API\AddIns\`
2. In Fusion: **Utilities > Add-Ins > Scripts and Add-Ins**, find
   `ExportRevisionStamper` under the Add-Ins tab, select it, click **Run**
   (check "Run on Startup" if you want it always available).
3. The command appears under **Utilities**.

## Notes / limitations

- The stamped revision comes from `Document.dataFile.versionNumber`, which
  only exists once a document has been saved to a Fusion (cloud) project. A
  document that's never been saved to the cloud stamps as version 1.
- 3MF export requires a Fusion API version that exposes
  `ExportManager.createC3MFExportOptions`. If your Fusion build doesn't have
  it, the add-in will tell you to use STEP or STL instead.
- This is a narrow first version: one command, one log file per output
  folder, no BOM/assembly batch export. It's meant to be the guard against
  outdated-revision handoffs, not a full PDM replacement.

## Development

The filename-templating and CSV-logging logic (`lib/naming.py`,
`lib/handoff_log.py`) has no Fusion API dependency and is unit tested:

```bash
pip install pytest
python3 -m pytest tests/ -q
```

## License

MIT — see [LICENSE](../LICENSE).
