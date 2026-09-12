# Profile: datasheet

## Signals
- A part number and a one-line function in the title ("EXM-500 Programmable Display Controller", "LM317 3-Terminal Adjustable Regulator").
- Feature bullets, pin configuration, absolute maximum ratings, electrical characteristics tables, waveforms or typical performance curves.
- Publisher logo on every page, data book page numbers (5-101), order or literature numbers (EXM-00500A, SNVS...).

## Typical content
- Front page: features, description, block diagram, pinout.
- Pin description table; functional description; register or command sections for programmable parts.
- Absolute maximum ratings, D.C./A.C. characteristics, test circuits, timing waveforms, typical curves, package outlines, ordering information.

## Custom steps
- **Stage 2:** record the part number, revision and family members covered; note if several parts share tables (column per variant).
- **Stage 4:** keep min/typ/max, units and test conditions in every characteristics row; note footnote markers on parameters. Timing waveforms get "measured from / to" tables. Typical curves get approximate key-point tables, never presented as limits.
- **Stage 4:** check that every timing symbol drawn in waveforms has a table row; list missing ones in a Transcriber's note.
- **Stage 6:** ask the reviewer to check edge choices of timing parameters and every characteristics cell.
- **Stage 8:** consolidated timing table, command/register cheat sheet, pin list by function, worked configuration example for programmable parts.

## Questions to ask
- Are all variants/package options needed, or only one?
- Should typical performance curves be tabulated (L2) or only described (L1)?

## Split suggestion
- Pinout and bus interface; architecture and system operation; functional/format sections; programming and commands; electrical limits (D.C.); A.C. timing and waveforms; packages and ordering.

## Useful extras
- Consolidated timing table; command cheat sheet; byte/code decode map; known inconsistencies; worked configuration example.
