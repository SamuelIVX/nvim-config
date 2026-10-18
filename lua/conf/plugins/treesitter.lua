-- Current Tree-sitter API: explicit parser installation and native highlighting.
return {
  "nvim-treesitter/nvim-treesitter",
  branch = "main",
  commit = "d4a9b23a383266bdb0bfb42d565f31e83f27be5e",
  lazy = false,
  build = ":TSUpdate",
  config = function()
    local ts = require("nvim-treesitter")
    ts.setup({})
    vim.treesitter.language.register("json", "jsonc")
    vim.api.nvim_create_autocmd("FileType", {
      group = vim.api.nvim_create_augroup("SamTreesitter", { clear = true }),
      pattern = {
        "c",
        "cpp",
        "python",
        "java",
        "html",
        "css",
        "javascript",
        "javascriptreact",
        "typescript",
        "typescriptreact",
        "json",
        "jsonc",
        "lua",
        "vim",
        "help",
        "query",
      },
      desc = "Enable Tree-sitter when the file's parser is installed",
      callback = function(event)
        local lang = vim.treesitter.language.get_lang(vim.bo[event.buf].filetype)
        if lang and vim.treesitter.language.add(lang) then
          vim.treesitter.start(event.buf, lang)
        end
      end,
    })
  end,
}
