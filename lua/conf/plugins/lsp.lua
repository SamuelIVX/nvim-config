-- Native LSP configuration plus profile-local, explicitly versioned Mason tools.
return {
  "neovim/nvim-lspconfig",
  tag = "v2.12.0",
  dependencies = {
    { "mason-org/mason.nvim", tag = "v2.3.1", opts = {} },
    { "mason-org/mason-lspconfig.nvim", tag = "v2.3.0" },
    { "hrsh7th/cmp-nvim-lsp", commit = "cbc7b02bb99fae35cb42f514762b89b5126651ef" },
  },
  config = function()
    vim.lsp.config("*", { capabilities = require("cmp_nvim_lsp").default_capabilities() })
    vim.lsp.config("lua_ls", {
      settings = {
        Lua = { diagnostics = { globals = { "vim" } }, workspace = { checkThirdParty = false } },
      },
    })
    vim.lsp.config("jdtls", {
      cmd = function(dispatchers, config)
        -- The launcher defaults to a 1 GB initial heap; start smaller on a 16 GB Mac.
        return vim.lsp.rpc.start(
          {
            "jdtls",
            "--jvm-arg=-Xms128m",
            "--jvm-arg=-Xmx1g",
            "-data",
            require("conf.java").workspace(assert(config.root_dir)),
          },
          dispatchers,
          {
            cwd = config.cmd_cwd,
            env = config.cmd_env,
            detached = config.detached,
          }
        )
      end,
    })
    if vim.env.NVIM_CONFIG_OPERATION == "verify" then
      -- Verification uses local tools only; Mason setup may refresh a stale registry.
      for _, identifier in ipairs(require("conf.tools").servers) do
        vim.lsp.enable(identifier:match("^([^@]+)"))
      end
    else
      require("mason-lspconfig").setup({
        ensure_installed = vim.env.NVIM_CONFIG_OPERATION and {} or require("conf.tools").servers,
      })
    end
  end,
}
