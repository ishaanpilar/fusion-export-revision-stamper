# Export Revision Stamper

A small Fusion 360 add-in that stamps the design's current revision onto
exported STEP/STL/3MF filenames — so a filename never lies about what
revision it is — and keeps a local log of every export as a handoff record.

Fusion tracks an internal version number but won't put it in the exported
filename, which is how folders end up with `bracket_final_v2_REAL.step`
and vendors cut the wrong revision. This add-in stamps the real, saved
revision onto every export automatically.

It's deliberately not a PDM system — one job, done well: the exported file
is always labeled with the right revision, and there's a record of it.

**→ [ExportRevisionStamper/](ExportRevisionStamper/) — the add-in, install
instructions, filename template reference, and known limitations.**

## Status

`v0.1.0` — the filename-templating and logging logic is unit tested, but
the Fusion API integration hasn't yet been run inside a live Fusion
session. See the [add-in README](ExportRevisionStamper/README.md#notes--limitations)
for what's verified and what isn't.

## License

MIT — see [LICENSE](LICENSE).
