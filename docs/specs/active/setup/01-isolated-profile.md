# Isolated Neovim profile

## Purpose
An original, portable configuration inspired by Magicalbat/Configs, with Tokyo
Night, a sidebar, fuzzy search, completion, bracket pairing, and language servers.

## Requirements and interface
- [verified] Launch `bin/nv [nvim arguments...]` with `NVIM_APPNAME=nvim-sam`.
- Link this repository to `~/.config/nvim-sam` and its launcher to `~/.local/bin/nv`.
- Keep default Neovim configuration, data, state, and caches separate.
- Lock plugin revisions. Pin Mason package versions separately from lazy-lock.json.
- Configure TypeScript/JavaScript/React, HTML, CSS, Python, C/C++, Lua, and Java.
- Use native LSP configuration, current Tree-sitter APIs, and built-in snippets.
- Give Java projects distinct workspace caches based on canonical absolute roots.
- Respect EditorConfig; keep swap protection and persistent undo.
- Use two spaces for web/Lua, four for Python/Java/C/C++.

## Non-goals
No GitHub publication, debugger, test runner, AI integrations, automatic formatting,
shell aliases, global NVIM_APPNAME, or project build configuration changes.
System executables are shared; profile isolation is not a security sandbox.

## Failure and update behavior
Report bootstrap failures without waiting for keyboard input. Missing language
servers do not prevent editing. Mason installation failures remain visible in
`:Mason` and its logs. Plugin and server updates are manual and verified before
recording new versions. Never replace existing configuration paths implicitly.

## Acceptance
Run syntax/launcher checks and headless assertions. Verify plugin health, parser
installation, per-language LSP requests, Java workspace separation, and isolated
standard paths. Report manual UI checks and unavailable runtimes honestly.
Measure memory separately for the editor and its child servers.
