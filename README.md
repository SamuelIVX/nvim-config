# Sam's Neovim configuration

An isolated Neovim profile with Tokyo Night, file navigation, search, completion,
and language servers. Launch **`nv`** for this setup; **`nvim`** keeps its default
profile. Requires Neovim 0.12+ with LuaJIT. macOS Apple Silicon is the tested host.

## Install

Install system tools with Homebrew:

```sh
brew install neovim tree-sitter-cli ripgrep fd stylua
```

Node/npm, Python 3.9+, a C compiler, and Java 21+ must be on PATH. On macOS the
Command Line Tools provide the C compiler. Keep project JDK/toolchain requirements
in Maven or Gradle; the server's runtime is separate from the project's target.

Clone this repository wherever you keep projects, then from its root run:

```sh
mkdir -p "$HOME/.config" "$HOME/.local/bin"
ln -s "$PWD" "$HOME/.config/nvim-sam"
ln -s "$PWD/bin/nv" "$HOME/.local/bin/nv"
bin/nv --headless -i NONE '+Lazy! restore' '+qa!'
bin/nv --headless -i NONE '+luafile tests/install.lua'
```

The links intentionally fail if their destinations already exist: inspect those
paths before replacing anything. Add `~/.local/bin` to PATH if needed. No shell
alias or global `NVIM_APPNAME` is needed. `bin/nv` also works directly.

## Getting started

Run `nv` and enter `:Tutor` for the interactive introduction. Run `nv .` from a
project directory, then press Space followed by `e` for its files.

| Action | Keys / command |
|---|---|
| Type / return to Normal mode | `i` / `Esc` |
| Save / save and quit / discard and quit | `:w` / `:wq` / `:q!`, then Enter |
| File sidebar | `Space e` |
| Find files / Git files / search text / buffers | `Space ff` / `Space fg` / `Space fr` / `Space fb` |
| Definition / documentation / diagnostic | `gd` / `K` / `Space k` |
| Rename / code actions | `Space rn` / `Space ca` |
| Previous / next buffer | `H` / `L` |
| Move between split windows | `Ctrl-h/j/k/l` |
| Completion selection | `Ctrl-n/p` or `Tab` / `Shift-Tab` |
| Accept selected completion / dismiss | `Enter` / `Ctrl-e` |
| Move through snippet placeholders | `Tab` / `Shift-Tab` when no completion menu is open |
| Plugins / language-server packages | `:Lazy` / `:Mason` |

Type `:checkhealth` for diagnostics. Some optional providers and unrelated package
ecosystems may be reported missing; this profile does not require them. Start
Neovim from the project root for project-wide search. C/C++ projects benefit from
their build system's `compile_commands.json` for accurate include paths.

## Isolation and ownership

| Content | Default location |
|---|---|
| Configuration, docs, plugin lock | This Git repository via `~/.config/nvim-sam` |
| Plugins, parsers, Mason tools | `~/.local/share/nvim-sam` |
| Undo, logs, state | `~/.local/state/nvim-sam` |
| Caches and per-project Java indexes | `~/.cache/nvim-sam` |

XDG environment variables can change these roots. Inspect them with
`:lua print(vim.inspect({vim.fn.stdpath('config'), vim.fn.stdpath('data'), vim.fn.stdpath('state'), vim.fn.stdpath('cache')}))`.
Only configuration belongs in Git. Runtime downloads and logs stay outside it.
System binaries are shared. Plugins and language servers run with your user's
permissions; the profile is not a security sandbox.

## Commands and checks

Run these from the repository root after installing plugins and tools:

```sh
sh -n bin/nv
stylua --check .
bin/nv --headless -i NONE '+luafile tests/check.lua'
bin/nv --headless -i NONE '+luafile tests/lsp.lua'
```

The last command creates temporary projects and tests real LSP completion,
navigation/hover where supported, and diagnostics. It may download Java build
metadata. HTML completion is checked without requiring validation diagnostics.
Set `NVIM_TEST_SERVER=jdtls` (or another configured server name) to test one server.
Tests exit nonzero on failure. There is no separate build/typecheck step for this
Lua configuration: syntax loading, formatting, and real startup are the checks.
GitHub Actions checks formatting, configuration, and tool installation on macOS;
the full language-server suite is a separate local integration check.

## Updates and rollback

Plugin versions and commits are explicit in their specs; `lazy-lock.json` records
resolved revisions. Edit the intended tag/commit, use `:Lazy update`, rerun checks,
and review the lockfile diff. `:Lazy restore` restores the recorded revisions.
The plugin manager itself is pinned too. Automatic update checking is disabled.

Mason is the installer for language servers; it does not manage project packages.
Its pinned inventory lives in `lua/conf/tools.lua`. Those versions are separate
from the plugin lock. Changing a version does not overwrite an already-installed
server automatically: uninstall that server in `:Mason`, then rerun
`tests/install.lua`. Inspect failures with `:MasonLog`.

Java starts with a 128 MB heap and a 1 GB maximum heap to reduce idle memory use.
Total process memory includes more than its heap. If a large project exhausts
that heap, raise `-Xmx1g` in the JDTLS configuration and repeat the Java checks.

After changing Tree-sitter revisions, run `:TSUpdate` and rerun installation/checks.
Keep [DEPENDENCIES.md](DEPENDENCIES.md) in sync with verified installations.

To disconnect the profile, remove only the two symlinks after verifying their
targets. The repository and downloaded profile data remain available. Plain
`nvim` continues to work independently. No GitHub remote is configured by setup.

## Map and design

- `init.lua`, `lua/conf/`: startup, preferences, keymaps, Java workspace naming,
  tool inventory, and plugin specifications.
- `bin/nv`: portable profile launcher; `tests/`: headless checks and installation.
- [Setup specification](docs/specs/active/setup/01-isolated-profile.md): requirements
  and acceptance criteria; [verification](docs/verification.md): actual results.

Inspired by [Magicalbat/Configs](https://github.com/Magicalbat/Configs), inspected at
`14e1f6c5821f9c15e1805f1dc929c227c484d9ae`. No license file was present in that
checkout, so this is an original implementation of the selected behavior rather
than a copy of its source. Third-party plugins retain their own licenses.
