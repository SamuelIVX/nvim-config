-- Verify installed tool receipts and parser binaries without requesting downloads.
local ok, err = xpcall(function()
  local registry = require("mason-registry")
  local mappings = require("mason-lspconfig.mappings").get_mason_map().lspconfig_to_package
  for _, identifier in ipairs(require("conf.tools").servers) do
    local name, version = identifier:match("^([^@]+)@(.+)$")
    local pkg = registry.get_package(assert(mappings[name], name))
    assert(not pkg:is_installing(), "Installation still in progress: " .. pkg.name)
    assert(pkg:get_receipt():is_present(), "Missing installation receipt: " .. pkg.name)
    assert(pkg:get_installed_version() == version, "Unexpected installed version: " .. pkg.name)
  end
  local installed = require("nvim-treesitter").get_installed("parsers")
  for _, lang in ipairs(require("conf.tools").parsers) do
    assert(vim.tbl_contains(installed, lang), "Missing parser binary: " .. lang)
  end
  print("Server receipts and parser binaries verified")
end, debug.traceback)
if not ok then
  io.stderr:write(err .. "\n")
  vim.cmd("cquit 1")
end
vim.cmd("qa!")
