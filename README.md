# Sam's Neovim configuration

An isolated Neovim profile with Tokyo Night, file navigation, search, completion,
and language servers. Launch **`nv`** for this setup; **`nvim`** keeps its default
profile. Supports macOS ARM64 and standard Fedora 43 x86-64. The installer preserves
compatible tools and can provide pinned, profile-owned fallbacks.

## Install

Python 3.12+ and Git are needed to run setup. From a clone of this repository:

```sh
python3 setup.py plan --install-tools
python3 setup.py apply --install-tools
python3 setup.py verify
```

`plan` does not write files or download anything. It reports prerequisites,
conflicts, selected tools, and the package command to run yourself. `apply` without
`--install-tools` requires compatible tools already present. The flag allows
checksum-verified official downloads of Neovim 0.12.5, Tree-sitter CLI 0.27.0,
and StyLua 2.5.2 into this profile; it does not install system packages.

On Fedora 43, install prerequisites yourself:

```sh
sudo dnf install python3 git gcc gcc-c++ make nodejs nodejs-npm java-21-openjdk-devel ripgrep fd-find curl tar gzip xz unzip wl-clipboard libatomic
```

On macOS, install Command Line Tools and these Homebrew prerequisites as needed:

```sh
brew install python git node openjdk ripgrep fd
export JAVA_HOME="$(brew --prefix openjdk)/libexec/openjdk.jdk/Contents/Home"
```

Node 22+, npm, Python 3.9+ on PATH for JDTLS, C/C++ compilers, make, and Java 21+
are required. Python running setup itself must be 3.12+. `JAVA_HOME` takes precedence
for Java; setup does not change Java alternatives or project Maven/Gradle targets.
Atomic editions and other CPU/OS combinations fail before installation.

Setup links this checkout to the XDG config profile and its launcher to
`~/.local/bin/nv`. Matching existing links can be adopted; different destinations
are refused. Add `~/.local/bin` to PATH if needed. No shell alias or global
`NVIM_APPNAME` is needed. `bin/nv` also works directly. The working Mac profile
can be adopted with `apply`; compatible Homebrew tools are preserved.

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

Managed fallback tools live in the profile's data directory under `tools/`, with
versioned installations and `tools/bin` selection links. Only `nv` prepends that
directory to its process PATH; ordinary `nvim` keeps its existing behavior.
An ownership receipt lives in the profile's state directory. Setup operations
are serialized by locking its parent directory, without leaving lock files.

## Commands and checks

Run these from the repository root after installing plugins and tools:

```sh
sh -n bin/nv
sh -n ci/check.sh
python3 -m unittest discover -s tests -p 'test_*.py'
uvx ruff==0.16.10 check setup.py tests/test_setup.py
uvx ruff==0.16.10 format --check setup.py tests/test_setup.py
stylua --check .
python3 setup.py verify
python3 setup.py verify --lsp
```

The last command creates temporary projects and tests real LSP completion,
navigation/hover where supported, and diagnostics. It may download Java build
metadata. HTML completion is checked without requiring validation diagnostics.
Set `NVIM_TEST_SERVER=jdtls` (or another configured server name) to test one server.
Tests exit nonzero on failure. There is no separate build/typecheck step for this
Lua configuration: syntax loading, formatting, and real startup are the checks.
GitHub Actions tests the complete restore and LSP suite on macOS ARM64 and a
digest-pinned Fedora 43 container running as non-root. It covers repeat apply,
default-editor isolation, disconnection, and purge. Graphical font and clipboard
behavior still needs a desktop session; headless CI cannot establish that.

## Updates and rollback

Plugin versions and commits are explicit in their specs; `lazy-lock.json` records
resolved revisions. Edit the intended tag/commit, use `:Lazy update`, rerun checks,
and review the lockfile diff. `:Lazy restore` restores the recorded revisions.
The plugin manager itself is pinned too. Automatic update checking is disabled.

Fallback tool pins are in `manifests/tools.json`. Setup does not automatically
rebind a link pointing at a different tool version. When deliberately changing a
pin, inspect and remove that tool's old selection link under the profile's
`tools/bin/`, then rerun `apply --install-tools`. Existing versioned downloads
remain available. A path inside `tools/` alone is not proof of installer ownership.

Mason is the installer for language servers; it does not manage project packages.
Its pinned inventory lives in `lua/conf/tools.lua`. Those versions are separate
from the plugin lock. Changing a version does not overwrite an already-installed
server automatically: uninstall that server in `:Mason`, then rerun
`scripts/install.lua` through `apply`. Inspect failures with `:MasonLog`.

Java starts with a 128 MB heap and a 1 GB maximum heap to reduce idle memory use.
Total process memory includes more than its heap. If a large project exhausts
that heap, raise `-Xmx1g` in the JDTLS configuration and repeat the Java checks.

After changing Tree-sitter revisions, run `:TSUpdate` and rerun installation/checks.
Keep [DEPENDENCIES.md](DEPENDENCIES.md) in sync with verified installations.

To disconnect the profile, run `python3 setup.py remove`. It removes only matching
managed links, retaining downloads and user state. Run `apply` to reconnect.

Close running `nv` sessions before `python3 setup.py remove --purge`. **Purge also
deletes this profile's tools, plugins, language servers, undo history, logs, and
caches.** It preserves the source checkout, plain Neovim data, and system packages.
Both removal modes require a matching setup receipt and refuse changed destinations
or redirected runtime roots. Purge does not follow nested links outside the profile.

Interrupted setup can leave completed tools or links in place. Errors identify
the failing step; inspect `plan` before retrying. No whole-operation rollback is
claimed. The source repository must remain at the same path while linked.

## Map and design

- `init.lua`, `lua/conf/`: startup, preferences, keymaps, Java workspace naming,
  tool inventory, and plugin specifications.
- `bin/nv`: portable profile launcher.
- `setup.py`, `manifests/`, `scripts/`: setup operations, official tool pins, and
  plugin/server restore and verification helpers. `tests/` contains regression checks.
- [Setup specification](docs/specs/active/setup/01-isolated-profile.md): requirements
  and acceptance criteria; [verification](docs/verification.md): actual results.
- [Portable installer specification](docs/specs/active/setup/02-portable-installer.md):
  macOS/Fedora 43 installation and removal requirements.

Inspired by [Magicalbat/Configs](https://github.com/Magicalbat/Configs), inspected at
`14e1f6c5821f9c15e1805f1dc929c227c484d9ae`. No license file was present in that
checkout, so this is an original implementation of the selected behavior rather
than a copy of its source. Third-party plugins retain their own licenses.
