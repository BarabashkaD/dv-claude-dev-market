# Profile: standard-spec

## Signals
- Standards bodies and identifiers (ISO, IEC, IEEE, ANSI, JEDEC, ECMA, ITU, RFC), "Specification", "Revision", normative language (shall, should, may).
- Numbered clauses (4.2.1), normative references, definitions, annexes (normative/informative).

## Typical content
- Scope, normative references, terms and definitions, requirements clauses, conformance.
- Frame/packet formats, state machines, message sequences, encoding tables, timing requirements.
- Annexes with examples, test methods, change history.

## Custom steps
- **Stage 2:** record the exact identifier, edition, date and status (draft, final, withdrawn); check for copyright or licence restrictions and confirm the user's intended use (personal notes vs distribution).
- **Stage 4:** keep clause numbers as heading numbers; keep normative keywords exactly (never paraphrase "shall"); tables of fields as bit-field or byte-offset tables; state machines as `stateDiagram-v2` plus transition tables; message exchanges as `sequenceDiagram`.
- **Stage 4:** mark each annex normative or informative as printed.
- **Stage 5:** check that every clause number in the table of contents has a heading and every defined term used in requirements is in the definitions list.
- **Stage 8:** requirements index (clause → shall statements), field-format quick tables, terms glossary.

## Questions to ask
- Full document or selected clauses?
- Is the output for private notes only (licence)?

## Split suggestion
- Front matter and definitions; one part per major clause group; annexes.

## Useful extras
- Shall-statement index; frame/field format cheat sheet; state and message summary.
