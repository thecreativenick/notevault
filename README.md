# notevault

A local-first Markdown notes app. Edit the same note in two offline browser profiles, sync,
and both edits survive.

## Status

Early scaffold. Done so far:

- An RGA text CRDT: Lamport-stamped character ids, tombstone deletes, idempotent apply and
  buffering of out-of-order ops. A fuzz test with three replicas making random offline edits,
  delivered shuffled, checks they always converge.
- `[[Wiki links]]` extraction (ignoring code spans and fences), a backlink index and
  broken-link report.

## Planned milestones

1. A CommonMark parser written from the spec (block structure first, then inlines with the
   delimiter-run algorithm) and an HTML renderer.
2. Storage: notes and op logs in SQLite; compact encoding of runs of characters.
3. Sync server (WebSocket) and a browser client storing ops in IndexedDB for offline work.
4. Full-text search index over 100,000 notes; tags; backlinks panel.
5. A sync-conflict fuzzer driving two Chrome profiles through Playwright.

## Success bar

The parser passes the CommonMark spec tests, searching 100,000 notes takes under 50 ms, and
10,000 fuzzed sync conflicts lose no text.

## Development

```bash
pip install -e .[dev]
pytest
```
