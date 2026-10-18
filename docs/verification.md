# Verification

## TL;DR

The isolated profile is installed locally. Plugin/tool installation and real LSP
requests passed on macOS ARM64. The repository is published publicly at
[SamuelIVX/nvim-config](https://github.com/SamuelIVX/nvim-config). Published commit
metadata uses GitHub noreply addresses. A tracked-file scan found no matching
credential patterns; this is not a guarantee against every possible secret.

## Checks performed

Portable installer work: clean-home macOS installation of all three pinned
fallback tools, repeated apply, configuration checks, the complete real LSP suite,
disconnect/reconnect, and purge passed locally. Adoption of the existing Mac
profile and its full LSP verification also passed. The 28-test installer suite,
Python formatting/lint, shell syntax, and Lua formatting passed.

[Hosted run 39099820980](https://github.com/SamuelIVX/nvim-config/actions/runs/39099820980)
passed lint plus full restore, repeat, LSP, disconnect/reconnect, and purge checks
on Fedora 43 x86-64 (non-root container) and macOS ARM64. Final implementation
commit `7ac220a` passed both
[push](https://github.com/SamuelIVX/nvim-config/actions/runs/39100218265) and
[PR](https://github.com/SamuelIVX/nvim-config/actions/runs/39100220916) workflows,
including the review fixes. The original profile checks below remain prior evidence.

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

The portable implementation's first CodeRabbit pass completed with two minor
findings. The missing Command Line Tools preflight was fixed with a regression
test. Automatic rebinding of older managed-tool aliases was declined: the spec
requires refusing unexpected targets, and directory membership alone does not
prove ownership. Explicit pin changes and manual selection-link removal are
documented.
The second implementation review completed with two minor findings: add the
Homebrew `JAVA_HOME` export to the Mac instructions, and syntax-check both shell
scripts separately in CI. Both were fixed and locally validated. No unresolved
major findings remain; automatic stale-alias rebinding remains intentionally
declined. The PR's latest checks cover the final documentation/workflow fixes.

### Original profile review

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

### PR feedback follow-up

The GitHub CodeRabbit review at `a462069` completed with no actionable inline
comments and a docstring coverage warning. Installer test fixtures, regression
contracts, and nested validation/probe helpers now have explanatory docstrings;
the remote coverage result must be rechecked after the next review.

Graphify's four inline findings count callees in `make_plan`, `apply`, `verify`,
and `main`. These functions coordinate existing, separately tested helpers.
The counts alone identify no broken behavior or unnecessary dependency, so no
wrapper layers or function splits were added solely to reduce the metric.

Graphify also suggested the old-default-Neovim assertion would fail on macOS.
The workflow explicitly puts a fake `nvim` reporting 0.11.6 on its restricted
PATH before `ci/check.sh` runs; Fedora uses its older distro package. The check
therefore deliberately verifies that managed tools affect `nv` alone. Existing
successful hosted runs cover both paths, so that assertion remains intact.

CodeRabbit's attached tool output also identified a shell assignment masking a
failed Homebrew Java-prefix lookup. The lookup now runs separately from `export`,
so the runner's error handling observes its exit status. Reported Markdown
heading spacing was corrected. No runtime behavior or test assertions changed;
documentation and workflow checks cover these edits without new test cases.

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
