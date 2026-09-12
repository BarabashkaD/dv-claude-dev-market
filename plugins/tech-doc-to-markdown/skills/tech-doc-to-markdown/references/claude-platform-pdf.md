# Claude Platform: PDF and File Input (reference only)

The user chose to keep the Claude API as reference material. This skill does not call the API unless the user explicitly asks. Use these facts to answer questions such as "could the API do this faster?" or to plan a future batch pipeline. Verify details against the current Claude API documentation (the `claude-api` skill) before writing code, because API shapes change.

## What the API accepts

- **PDF as a document content block** in a Messages API request, either base64 inline (`{"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": "<base64>"}}`) or by reference to an uploaded file (`{"type": "document", "source": {"type": "file", "file_id": "..."}}`). Place the document block before the text instruction.
- **Limits:** about 32 MB per request and up to 600 pages per document (100 pages for models with a 200k context window). Both the text and the page images are understood, so scanned pages work.
- **Files API:** upload once and reuse the `file_id` across requests. It is out of beta in current SDKs (`client.files.upload(...)`; older examples use `client.beta.files` with a beta header). Up to 500 MB per file; file operations are free, content used in messages is billed as input tokens.
- **Citations:** `"citations": {"enabled": true}` on each document block makes answers cite page ranges (`page_location` with 1-indexed start and end pages). Citations cannot be combined with structured output formats.
- **Batches:** the Message Batches API processes many requests asynchronously at half price; results come back in any order, keyed by `custom_id`.
- **Models:** the current default recommendation is Claude Opus 5 (`claude-opus-5`) with adaptive thinking; long outputs should stream.

## How it could fit this workflow (only if the user asks)

| Stage | Possible API use | Caveat |
|---|---|---|
| Classification | Send the first pages with citations for a fast summary card | Needs credentials and approval of cost |
| Draft extraction | Per-chapter extraction of prose and tables with page citations | Still needs render-based checking of numbers and diagrams |
| Large archives | Batch many documents for L1 drafts | Diagrams, waveforms and grids still need the in-session L2/L3 process |

## Credentials

The SDKs read `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, or an `ant auth login` profile. Check with `ant auth status` when the `ant` CLI is installed. Never ask the user to paste a key into chat; point them to setting the environment variable or `ant auth login`.
