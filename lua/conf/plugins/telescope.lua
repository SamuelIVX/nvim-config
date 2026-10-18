-- Search files, Git files, project text, and open buffers with Telescope.
return {
  "nvim-telescope/telescope.nvim",
  tag = "v0.2.1",
  dependencies = {
    { "nvim-lua/plenary.nvim", commit = "74b06c6c75e4eeb3108ec01852001636d85a932b" },
  },
  cmd = "Telescope",
  keys = {
    { "<leader>ff", "<cmd>Telescope find_files<cr>", desc = "Find files" },
    { "<leader>fg", "<cmd>Telescope git_files<cr>", desc = "Find Git files" },
    { "<leader>fr", "<cmd>Telescope live_grep<cr>", desc = "Search project text" },
    { "<leader>fb", "<cmd>Telescope buffers<cr>", desc = "Find buffers" },
  },
  opts = {},
}
