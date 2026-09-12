# dv-claude-dev-market

BarabashkaD's personal marketplace of Claude Code plugins.

## Usage

Add this marketplace in Claude Code:

```
/plugin marketplace add BarabashkaD/dv-claude-dev-market
```

Then install a plugin from it:

```
/plugin install <plugin-name>@dv-claude-dev-market
```

## Catalog

### Documentation

| Plugin | What it does |
|---|---|
| [`tech-doc-to-markdown`](plugins/tech-doc-to-markdown) | Converts technical documentation — PDF, scanned PDF, DjVu, DOC/DOCX, RTF, ODT, EPUB, page images — into faithful, verified Markdown. Tables, block diagrams, timing diagrams, pinouts, register maps and dot matrices all become text. Classifies first, transcribes in a cold-context subagent, then verifies with self-check scripts and an adversarial review. |

### Tooling

| Plugin | What it does |
|---|---|
| [`python-venv-manager`](plugins/python-venv-manager) | One virtual environment per skill under a per-user Claude venvs directory, reused across sessions and projects instead of rebuilt each time. Includes a `PreToolUse` hook that blocks bare `python`/`pip` invocations. Linux, macOS, Windows. |

## Structure

Each plugin lives under `plugins/<plugin-name>/` and is registered in
`.claude-plugin/marketplace.json`.

A marketplace distributes **plugins** — that is the only installable unit.
Skills, MCP servers, commands, agents and hooks are *components inside* a
plugin, not separate top-level categories of the marketplace. A plugin whose
only payload is a skill is a normal, supported shape; grouping in this README
and the `category` / `keywords` fields in the manifests are what provide the
category view.

```
dv-claude-dev-market/
├── .claude-plugin/
│   └── marketplace.json
└── plugins/
    └── <plugin-name>/
        ├── .claude-plugin/
        │   └── plugin.json   # required manifest
        ├── skills/           # skills live here, one dir each with SKILL.md
        ├── commands/         # slash commands (.md)
        ├── agents/           # subagents (.md)
        ├── hooks/            # hooks.json + scripts
        ├── .mcp.json         # MCP servers
        └── README.md
```

## Adding a new plugin

1. Create `plugins/<plugin-name>/` with a `.claude-plugin/plugin.json` and
   its components (skills, commands, hooks, etc.) at the plugin root.
2. Add an entry for it in `.claude-plugin/marketplace.json`:
   ```json
   {
     "name": "<plugin-name>",
     "description": "...",
     "version": "1.0.0",
     "category": "documentation",
     "keywords": ["...", "..."],
     "source": "./plugins/<plugin-name>"
   }
   ```
   Keep `category` and `keywords` in step with the plugin's own
   `.claude-plugin/plugin.json`, and add the plugin to the catalog above.
3. Validate before pushing — this checks both manifests and the components:
   ```
   claude plugin validate .
   ```
4. Commit and push.
5. On any machine: `/plugin marketplace add BarabashkaD/dv-claude-dev-market`
   (or `/plugin marketplace update dv-claude-dev-market` if already added),
   then `/plugin install <plugin-name>@dv-claude-dev-market`.
