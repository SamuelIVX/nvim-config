# Verification

## TL;DR
The isolated profile is installed locally. Plugin/tool installation and real LSP
requests passed on macOS ARM64. The repository is published publicly at
[SamuelIVX/nvim-config](https://github.com/SamuelIVX/nvim-config). Published commit
metadata uses GitHub noreply addresses. A tracked-file scan found no matching
credential patterns; this is not a guarantee against every possible secret.

## Checks performed
- Shell launcher syntax, Lua formatting/syntax, startup, profile directory checks,
  theme, keymaps, sidebar open/close, file picker, bracket pairing, built-in snippet
  expansion, EditorConfig precedence, and attached Tree-sitter highlighting passed.
- All seven Mason package receipt versions match the selected versions; all 14
  selected parser binaries are installed. JSONC reuses JSON's parser.
- TypeScript, Python, C, Lua, and Java returned completion, definition, hover, and
  diagnostics in disposable projects. HTML completion and CSS completion/diagnostics
  passed. Two Java projects with identical folder names passed independently.
- Clipboard round trip passed while preserving the prior clipboard text. The
  launcher forwarded a filename containing spaces correctly.
- Default `nvim` retained its separate config/data locations. Native ARM64 Neovim
  and the ARM64 slice of clangd are installed.
- Health reports for Mason, mason-lspconfig, Tree-sitter, Telescope, and native LSP
  contained no errors after loading the requested plugins. Optional ecosystem
  tools and Doxygen filetypes produced warnings; this setup does not require them.

## Review
CodeRabbit's first completed review reported one major and one minor installation
check issue. Both were independently confirmed against plugin source and fixed:
wait for Mason installation completion and validate receipts/versions; check
Tree-sitter parser binaries rather than the union of parsers and queries.
Installation, editor behavior, and the complete LSP suite passed again afterward.
The second external review completed. Its documentation-status correction is
included here. Its other minor suggestion was to automatically replace installed
servers when their versions differ. That suggestion was declined: the documented
update policy deliberately requires an explicit uninstall/reinstall, and the
installer fails clearly on mismatches instead of overwriting an existing tool.
No unresolved major findings remain. Two external review passes were performed.

## Limits
One idle snapshot measured about 17 MiB RSS for the editor. With a tiny Java
project, the editor measured about 23 MiB and its Java server about 1,045 MiB after
initialization. Before the heap adjustment the Java server measured about 2,212
MiB. These are short snapshots, not peak-memory or large-project benchmarks.

Checks used headless Neovim and real server processes. Visual appearance in Sam's
interactive Terminal.app remains unverified. Hosted check results are available
in [GitHub Actions](https://github.com/SamuelIVX/nvim-config/actions).
The tests cover small projects, not large repository indexing or every supported
language dialect. Java can need a larger heap for large projects.
