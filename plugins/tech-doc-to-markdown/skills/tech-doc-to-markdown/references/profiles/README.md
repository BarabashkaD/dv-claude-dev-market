# Document Profiles

A profile adapts the general workflow to one document type. Classification (SKILL.md Stage 2) picks the profile whose signals best match the title page and first pages; when two fit, use the one covering most of the content and borrow steps from the other. When none fits, use `generic.md` and consider creating a new profile afterwards.

| Profile | Typical documents |
|---|---|
| `datasheet.md` | IC and component datasheets, data book chapters |
| `reference-manual.md` | Programming, user and reference manuals, API and protocol references for devices and software |
| `service-manual.md` | Service and repair manuals, schematics, parts lists, adjustment procedures |
| `standard-spec.md` | Standards, specifications, RFC-style protocol documents |
| `application-note.md` | Application notes, design guides, white papers, tutorials |
| `generic.md` | Anything else |

## Adding a profile

Copy this template to `<type>.md` and fill it in. Keep it short; it is read on every matching document.

```markdown
# Profile: <type>

## Signals
- <title words, publisher patterns, section names that identify this type>

## Typical content
- <what these documents contain and where>

## Custom steps
- <extra work beyond the general workflow, with the stage it belongs to>

## Questions to ask
- <type-specific clarifications for Stage 2>

## Split suggestion
- <natural parts for this type>

## Useful extras
- <quick-reference aids that pay off for this type>
```
