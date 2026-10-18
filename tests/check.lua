-- Headless regression checks for configuration, isolation, and Java workspaces.
local ok, err = xpcall(function()
  assert(vim.env.NVIM_APPNAME == "nvim-sam", "Launcher must select the isolated profile")
  for _, kind in ipairs({ "config", "data", "state", "cache" }) do
    assert(vim.fn.stdpath(kind):match("/nvim%-sam$"), kind .. " escaped profile")
  end
  for _, path in ipairs(vim.fn.glob("**/*.lua", false, true)) do
    assert(loadfile(path))
  end
  assert(vim.g.colors_name == "tokyonight-night")
  assert(vim.o.swapfile and vim.o.undofile)
  assert(vim.g.mapleader == " ")
  for _, keys in ipairs({ " e", " ff", " fr", " fb", " rn", " ca" }) do
    assert(vim.fn.maparg(keys, "n") ~= "", "Missing mapping: " .. keys)
  end
  local workspace = require("conf.java").workspace
  assert(workspace("/tmp/one/project") ~= workspace("/tmp/two/project"), "Java workspace collision")
  assert(workspace("/tmp/one/project") == workspace("/tmp/one/project"), "Unstable Java workspace")
  local dir = vim.fn.tempname()
  vim.fn.mkdir(dir, "p")
  assert(vim.uv.fs_symlink(dir, dir .. "-link"))
  assert(workspace(dir) == workspace(dir .. "-link"), "Java symlink roots must share workspace")
  vim.fn.delete(dir .. "-link")
  vim.fn.delete(dir, "d")
  require("lazy").load({
    plugins = { "nvim-tree.lua", "telescope.nvim", "nvim-cmp", "ultimate-autopair.nvim" },
  })
  assert(require("telescope.builtin").live_grep)
  assert(require("nvim-tree.api").tree.toggle)
  assert(require("cmp").get_config().snippet.expand)
  require("nvim-tree.api").tree.open()
  assert(require("nvim-tree.api").tree.is_visible(), "File sidebar did not open")
  require("nvim-tree.api").tree.close()
  require("telescope.builtin").find_files()
  assert(vim.bo.filetype == "TelescopePrompt", "File picker did not open")
  require("telescope.actions").close(vim.api.nvim_get_current_buf())
  vim.cmd("enew")
  vim.api.nvim_feedkeys(vim.api.nvim_replace_termcodes("<Esc>i(", true, false, true), "xt", false)
  assert(vim.api.nvim_get_current_line() == "()", "Bracket pairing failed")
  vim.api.nvim_buf_set_lines(0, 0, -1, false, { "" })
  vim.api.nvim_win_set_cursor(0, { 1, 0 })
  vim.snippet.expand("hello ${1:name}!")
  assert(vim.api.nvim_get_current_line() == "hello name!", "Snippet expansion failed")
  vim.snippet.stop()
  vim.cmd("enew!")
  local project = vim.fn.tempname()
  vim.fn.mkdir(project, "p")
  vim.fn.writefile(
    { "root = true", "[*]", "indent_style = space", "indent_size = 3" },
    project .. "/.editorconfig"
  )
  vim.fn.writefile({ "const value = 1;" }, project .. "/test.ts")
  vim.cmd.edit(vim.fn.fnameescape(project .. "/test.ts"))
  assert(vim.bo.shiftwidth == 3, "EditorConfig must override language defaults")
  assert(
    vim.treesitter.highlighter.active[vim.api.nvim_get_current_buf()],
    "Parser highlighting did not attach"
  )
  vim.cmd("bwipeout!")
  vim.fn.delete(project, "rf")
  assert(vim.v.errmsg == "", vim.v.errmsg)
  print("Configuration checks passed")
end, debug.traceback)
if not ok then
  io.stderr:write(err .. "\n")
  vim.cmd("cquit 1")
end
vim.cmd("qa!")
