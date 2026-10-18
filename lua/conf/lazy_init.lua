-- Install the pinned plugin manager; keep all downloads in this profile's data.
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.uv.fs_stat(lazypath) then
  assert(vim.env.NVIM_CONFIG_OPERATION ~= "verify", "Missing plugin manager; run setup.py apply")
  local output = vim.fn.system({
    "git",
    "clone",
    "--filter=blob:none",
    "--branch=v11.17.5",
    "https://github.com/folke/lazy.nvim.git",
    lazypath,
  })
  if vim.v.shell_error ~= 0 then
    error("lazy.nvim download failed: " .. output)
  end
end
vim.opt.rtp:prepend(lazypath)
require("lazy").setup({
  spec = { { "folke/lazy.nvim", tag = "v11.17.5" }, { import = "conf.plugins" } },
  checker = { enabled = false },
  change_detection = { notify = false },
  install = { missing = vim.env.NVIM_CONFIG_OPERATION ~= "verify" },
})
