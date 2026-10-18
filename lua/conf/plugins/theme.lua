-- Tokyo Night Night matches the terminal's existing palette.
return {
  "folke/tokyonight.nvim",
  tag = "v4.14.1",
  lazy = false,
  priority = 1000,
  config = function()
    vim.cmd.colorscheme("tokyonight-night")
  end,
}
