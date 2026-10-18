-- Restore exact locked plugin commits and fail if the operation did not complete.
local ok, err = xpcall(function()
  local lock_path = vim.fn.stdpath("config") .. "/lazy-lock.json"
  local original = table.concat(vim.fn.readfile(lock_path), "\n")
  local lock = vim.json.decode(original)
  require("lazy").restore({ wait = true, show = false })
  for name, revision in pairs(lock) do
    local source = vim.fn.stdpath("data") .. "/lazy/" .. name
    local actual = vim.fn.system({ "git", "-C", source, "rev-parse", "HEAD" })
    assert(
      vim.v.shell_error == 0 and vim.trim(actual) == revision.commit,
      "Plugin restore failed: " .. name
    )
  end
  assert(
    table.concat(vim.fn.readfile(lock_path), "\n") == original,
    "Plugin restore changed the lockfile"
  )
  print("Locked plugins restored")
end, debug.traceback)
if not ok then
  io.stderr:write(err .. "\n")
  vim.cmd("cquit 1")
end
vim.cmd("qa!")
