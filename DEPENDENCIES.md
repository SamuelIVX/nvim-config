# Dependency inventory

## TL;DR
Plugin specs and `lazy-lock.json` select editor code; `lua/conf/tools.lua` selects
Mason server versions and parser languages. Downloads remain outside this repo.

## System tools verified on this Mac

Neovim 0.12.5 (Homebrew 0.12.5_1, native ARM64), Tree-sitter CLI 0.27.0,
ripgrep 15.2.0, fd 10.4.2, StyLua 2.5.2, Python 3.14.2, Java 26.0.2.1,
and Apple clang 21.0.0. Node/npm are supplied by the existing shell environment;
Mason health detected Node 22.15.0 and npm 10.9.2 during verification.
Homebrew reported Neovim already current after refreshing its metadata.

## Portable setup

`manifests/tools.json` pins official Neovim 0.12.5, Tree-sitter CLI 0.27.0, and
StyLua 2.5.2 artifacts and published SHA-256 digests for macOS ARM64 and Linux
x86-64. Compatible existing tools are preserved; fallbacks stay profile-local.
The manifest records minimum versions separately from managed fallback versions.
Python 3.12+ runs the installer; Node 22+, npm, Java 21+, compilers, and other
prerequisites are supplied by the host. Ruff 0.16.10 is development-only.

`manifests/fedora.json` selects an immutable official Fedora 43 image index. CI
uses its Linux x86-64 image and runs profile setup as non-root. The system's older
Neovim remains separate. See the verification document for actual acceptance
results; dependency pins alone do not prove platform compatibility.

## Plugin selections

| Repository | Tag / full commit |
|---|---|
| folke/lazy.nvim | v11.17.5 |
| folke/tokyonight.nvim | v4.14.1 |
| nvim-tree/nvim-tree.lua | nvim-tree-v1.18.0 |
| nvim-telescope/telescope.nvim | v0.2.1 |
| mason-org/mason.nvim | v2.3.1 |
| mason-org/mason-lspconfig.nvim | v2.3.0 |
| neovim/nvim-lspconfig | v2.12.0 |
| hrsh7th/nvim-cmp | v0.0.2 |
| nvim-treesitter/nvim-treesitter | d4a9b23a383266bdb0bfb42d565f31e83f27be5e |
| hrsh7th/cmp-nvim-lsp | cbc7b02bb99fae35cb42f514762b89b5126651ef |
| nvim-tree/nvim-web-devicons | ec309a0eaff6ea967e58c275996155ab5c16938d |
| nvim-lua/plenary.nvim | 74b06c6c75e4eeb3108ec01852001636d85a932b |
| altermo/ultimate-autopair.nvim | 6b58234de921437836efe27714b2026ed2ee235a |

## Installed Mason packages

| Package | Version | LSP name |
|---|---|---|
| typescript-language-server | 6.0.2 | ts_ls |
| html-lsp | 4.10.0 | html |
| css-lsp | 4.10.0 | cssls |
| pyright | 1.1.414 | pyright |
| clangd | 23.1.0 | clangd |
| lua-language-server | 3.19.2 | lua_ls |
| jdtls | 1.61.0 | jdtls |

The Mason receipt versions were queried after installation. npm packages can have
their own transitive dependencies; this table is not a transitive dependency lock.
Parser revisions are selected by the pinned Tree-sitter plugin. JSONC uses the
JSON parser, since this Tree-sitter revision has no separate JSONC parser.
