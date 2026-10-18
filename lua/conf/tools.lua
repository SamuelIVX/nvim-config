-- Single inventory for server installation, parser setup, and verification.
return {
  servers = {
    "ts_ls@6.0.2",
    "html@4.10.0",
    "cssls@4.10.0",
    "pyright@1.1.414",
    "clangd@23.1.0",
    "lua_ls@3.19.2",
    "jdtls@1.61.0",
  },
  parsers = {
    "c",
    "cpp",
    "python",
    "java",
    "html",
    "css",
    "javascript",
    "typescript",
    "tsx",
    "json",
    "lua",
    "vim",
    "vimdoc",
    "query",
  },
}
