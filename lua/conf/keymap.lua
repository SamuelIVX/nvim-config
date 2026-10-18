-- Stable editor shortcuts; plugin shortcuts live with their plugin specs.
vim.g.mapleader = " "
vim.g.maplocalleader = " "
vim.keymap.set("n", "<Space>", "<Nop>")
for key, direction in pairs({ h = "h", j = "j", k = "k", l = "l" }) do
  vim.keymap.set(
    "n",
    "<C-" .. key .. ">",
    "<C-w>" .. direction,
    { desc = "Focus " .. direction .. " window" }
  )
end
vim.keymap.set("n", "<C-d>", "<C-d>zz", { desc = "Scroll down and center" })
vim.keymap.set("n", "<C-u>", "<C-u>zz", { desc = "Scroll up and center" })
vim.keymap.set("n", "H", "<cmd>bprevious<cr>", { desc = "Previous buffer" })
vim.keymap.set("n", "L", "<cmd>bnext<cr>", { desc = "Next buffer" })
vim.keymap.set("n", "<leader>rn", vim.lsp.buf.rename, { desc = "Rename symbol" })
vim.keymap.set({ "n", "x" }, "<leader>ca", vim.lsp.buf.code_action, { desc = "Code action" })
vim.keymap.set("n", "<leader>k", vim.diagnostic.open_float, { desc = "Show diagnostic" })
vim.api.nvim_create_autocmd("LspAttach", {
  group = vim.api.nvim_create_augroup("SamLspKeys", { clear = true }),
  desc = "Set language navigation keys in attached buffers",
  callback = function(event)
    vim.keymap.set(
      "n",
      "gd",
      vim.lsp.buf.definition,
      { buffer = event.buf, desc = "Go to definition" }
    )
    vim.keymap.set(
      "n",
      "K",
      vim.lsp.buf.hover,
      { buffer = event.buf, desc = "Symbol documentation" }
    )
  end,
})
