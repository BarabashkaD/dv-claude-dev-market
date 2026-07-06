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

## Structure

Each plugin lives under `plugins/<plugin-name>/` and is registered in
`.claude-plugin/marketplace.json`.

```
dv-claude-dev-market/
├── .claude-plugin/
│   └── marketplace.json
└── plugins/
    └── <plugin-name>/
        ├── .claude-plugin/
        │   └── plugin.json
        ├── skills/
        ├── commands/
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
     "source": "./plugins/<plugin-name>"
   }
   ```
3. Commit and push.
4. On any machine: `/plugin marketplace add BarabashkaD/dv-claude-dev-market`
   (or `/plugin marketplace update dv-claude-dev-market` if already added),
   then `/plugin install <plugin-name>@dv-claude-dev-market`.
