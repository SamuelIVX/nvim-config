# Portable Neovim setup for macOS and Fedora 43

## TL;DR
Implemented on the feature branch; acceptance evidence is recorded in
[verification](../../../verification.md). Extend this repository with a Python standard-library
installer supporting preview, explicit tool installation, verification, safe
disconnection, and optional complete profile removal. Keep the existing look,
keybindings, plugin pins, language servers, and independent `nv` profile.

This extends [the isolated-profile specification](01-isolated-profile.md).
The plan received a completed CodeRabbit review with zero findings. Implementation
requires its own review and acceptance evidence before completion.

## Purpose and success criteria
Restore the same Neovim configuration on Sam's Mac and Fedora workstation without
copying binaries between operating systems or replacing unrelated configuration.
A clean supported machine can install prerequisites, preview the operation, apply
the setup, verify it, and repeat apply without unnecessary changes. Both normal
removal and explicit purge must preserve the repository and default Neovim data.

## Evidence and supported platforms
- [verified] The existing macOS workflow passed at `90f3dd1`:
  [hosted result](https://github.com/SamuelIVX/nvim-config/actions/runs/39097306823).
- [verified] Fedora 43 lists Neovim 0.11.6 and Tree-sitter CLI 0.25.10. This
  configuration requires Neovim 0.12+; its pinned Tree-sitter plugin requires CLI
  0.26.1+. Distribution packages alone do not satisfy those requirements.
- [verified] Official release APIs provide platform artifacts and SHA-256 digests
  for Neovim 0.12.5, Tree-sitter CLI 0.27.0, and StyLua 2.5.2.
- [verified] The current agent-setup Fedora container pin selects Fedora 44;
  independent Fedora 43 testing is required here.
- [verified] Sam's dotfiles configure Hyprland, Kitty, JetBrains Mono Nerd Font,
  and Wayland clipboard tools. They do not prove the installed machine's state.
- [assumed] First-version targets are macOS ARM64 and standard Fedora 43 x86-64.
  Detect OS, release, CPU, and Atomic status at runtime. Unsupported systems and
  Atomic editions fail clearly before changes. The actual Fedora host remains
  unverified until detection runs there.

## Public interface
Require Python 3.12+; add `setup.py` with these commands:

```sh
python3 setup.py plan --install-tools
python3 setup.py apply --install-tools
python3 setup.py verify
python3 setup.py verify --lsp
python3 setup.py remove
python3 setup.py remove --purge
```

### Preview and installation
- `plan` is read-only and performs no downloads or directory creation. Report
  prerequisites, selected executables, proposed downloads, link changes, and
  conflicts. `--install-tools` previews the additional managed-tool actions.
- `apply` preflights prerequisites and all destinations, connects the profile,
  restores locked plugins, and installs the existing server/parser inventory.
- `--install-tools` explicitly permits downloading missing or incompatible
  Neovim, Tree-sitter CLI, and StyLua. Without the flag, report missing tools and
  stop before making changes.
- Use clear nonzero exits for unsupported systems, missing prerequisites,
  conflicts, and failed installation or verification.

### Verification and removal
- `verify` checks selected executable versions, isolated paths, plugin revisions,
  Mason receipts, parser binaries, and existing editor behavior checks. Check
  prerequisites before startup; verification must not silently install tools.
- `verify --lsp` additionally runs the real language-server tests. Explain that
  Java project imports may download build metadata.
- `remove` disconnects recognized configuration and launcher links.
- `remove --purge` additionally deletes this profile's managed tools, plugins,
  servers, undo history, logs, and caches. Print the exact deletion paths.
  The purge flag is explicit authorization for that profile data deletion.
- Never remove the configuration repository, shared system packages, shell
  configuration, or the default Neovim profile.

## Dependency ownership and selection
Preserve compatible existing tools. Managed fallbacks use the already tested
versions: Neovim 0.12.5, Tree-sitter CLI 0.27.0, and StyLua 2.5.2.

Store official versioned release URLs, architecture-specific artifact names, and
published SHA-256 digests in a committed manifest for both supported platforms.
Use Neovim tar archives, Tree-sitter release binaries, and StyLua release archives;
avoid AppImages and their FUSE dependency. Never fetch an unpinned `latest` artifact
or trust a checksum retrieved only alongside an unreviewed runtime download.

Verify bytes before extraction. Reject absolute paths, traversal, and unsafe
archive links. Stage into temporary directories and publish only completed,
validated installations atomically. Interrupted downloads must not become the
selected executables. Preserve successful tool downloads for retry.

System prerequisites remain human-managed:
- Fedora: print the required `dnf` command for Python, Git, C/C++ compilers, make,
  Node/npm, Java 21+, ripgrep, fd, archive utilities, Wayland clipboard tools, and
  required runtime libraries. Validate package names in the Fedora 43 fixture.
- macOS: print Homebrew prerequisites and identify missing Command Line Tools.
- Never invoke sudo, configure repositories, upgrade the distribution, modify
  global PATH, or change Java alternatives automatically.

## Isolation and existing behavior
Update `bin/nv` to expose managed tools only within the launched profile's process
environment. It must select the managed compatible Neovim when Fedora's normal
`nvim` is too old, while preserving the ordinary `nvim` command outside `nv`.
Preserve compatible existing Mac tools and the current profile's behavior.

Honor XDG config/data/state/cache roots and keep all generated content under
`nvim-sam`. Record selected tools and managed paths in a profile-local receipt
outside Git. Keep the existing plugin lock and seven language-server pins.
Continue honoring `JAVA_HOME`; probe the runtime JDTLS actually selects and
report an incompatible Java runtime rather than changing global Java settings.

Keep Tokyo Night and current shortcuts. Reuse Kitty's configured Nerd Font and
Wayland clipboard tools. Do not modify the dotfiles or agent-setup repositories.
Promote the existing installation helper out of the tests directory and update
its callers. Keep one authoritative parser/server inventory.

## Conflicts, repeat runs, and failure recovery
- Refuse differing files, directories, and symlinks at managed destinations.
  Accept existing links only when they resolve to this repository's expected
  targets, including the exact matching links on the existing Mac.
- Repeated apply must avoid duplicate links, preserve compatible tools, and
  leave the source repository and lockfile unchanged.
- Record ownership before reporting successful setup. Do not overwrite unknown
  installations or treat an incomplete tool directory as a valid installation.
- Preflight destination conflicts before mutations. If a later step fails,
  identify completed steps and leave installed downloads recoverable; do not
  claim the whole operation was atomic. Do not replace concurrent path changes.
- Surface partial plugin/server failures with a nonzero result and actionable
  logs. Validate Mason completion and receipts rather than directory presence.
- Removal checks the recorded paths and current link targets and refuses changed
  destinations. Purge preflights every deletion, rejects redirected profile
  roots, and never follows nested symlinks into external directories.

## Test and acceptance plan
Use temporary homes and standard-library installer tests for preview immutability,
platform detection, compatible and incompatible tool selection, checksum failure,
unsafe archives, interrupted installation, conflicting destinations, XDG roots,
paths containing spaces, repeat apply, and removal/purge protections.

Verify clean installations as a non-root user on:
1. A digest-pinned Fedora 43 x86-64 container with Fedora's older Neovim present.
   Prove `nv` selects its managed runtime and plain `nvim` remains unchanged.
2. macOS ARM64, covering both fresh setup and reuse of compatible tools.

On both targets, restore locked plugins, verify all actual parser binaries and
server receipts, run existing editor behavior checks, and run the full real LSP
suite including two Java roots with matching folder names. Repeated apply must
produce no unnecessary managed-path changes and no source/lockfile drift.

Desktop clipboard and font checks require a graphical session. Report these
separately from headless container results. Do not claim Fedora workstation
validation based on hosted CI. Local container tools were unavailable during
planning; hosted Fedora execution remains future acceptance work.

## Delivery and non-goals
Implement on a feature branch. Run the required CodeRabbit review and obtain green
macOS/Fedora CI before presenting implementation as complete. Update the setup
specs, README, dependency inventory, verification evidence, and machine context.
Prepare a draft PR; merging remains separate.

Linux ARM64, other distributions, Fedora Atomic installation, new editor features,
desktop configuration changes, and automatic global package management are not
included. Profile isolation is not a security sandbox.

## Sources
- [Fedora Neovim packages](https://packages.fedoraproject.org/pkgs/neovim/neovim/)
- [Fedora Tree-sitter CLI packages](https://packages.fedoraproject.org/pkgs/rust-tree-sitter-cli/tree-sitter-cli/index.html)
- [Neovim 0.12.5 release](https://github.com/neovim/neovim/releases/tag/v0.12.5)
- [Tree-sitter 0.27.0 release](https://github.com/tree-sitter/tree-sitter/releases/tag/v0.27.0)
- [StyLua 2.5.2 release](https://github.com/JohnnyMorganz/StyLua/releases/tag/v2.5.2)
- [Sam's desktop dotfiles](https://github.com/SamuelIVX/dotfiles)
