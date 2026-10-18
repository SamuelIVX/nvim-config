-- Stable Java index directories distinguish roots even when folder names match.
local M = {}

---Return a project-specific JDTLS workspace outside the project's source tree.
---@param root string Absolute project root
---@return string workspace Absolute cache directory
function M.workspace(root)
  local canonical = vim.uv.fs_realpath(root) or vim.fs.normalize(root)
  return vim.fn.stdpath("cache") .. "/jdtls/" .. vim.fn.sha256(canonical)
end

return M
