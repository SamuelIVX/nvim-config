-- File sidebar and Nerd Font icons, opened only when requested.
return {
  "nvim-tree/nvim-tree.lua",
  tag = "nvim-tree-v1.18.0",
  dependencies = {
    { "nvim-tree/nvim-web-devicons", commit = "ec309a0eaff6ea967e58c275996155ab5c16938d" },
  },
  cmd = { "NvimTreeToggle", "NvimTreeFindFile" },
  keys = { { "<leader>e", "<cmd>NvimTreeToggle<cr>", desc = "Toggle file sidebar" } },
  opts = {},
}
