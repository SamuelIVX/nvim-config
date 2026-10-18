-- Install profile-local parsers and servers, checking completed installation receipts.
local ok, err = xpcall(function()
  local registry = require("mason-registry")
  local refreshed, refresh_ok = false, false
  registry.refresh(function(success)
    refresh_ok = success
    refreshed = true
  end)
  assert(
    vim.wait(120000, function()
      return refreshed
    end, 100),
    "Mason registry refresh timed out"
  )
  assert(refresh_ok, "Mason registry refresh failed; inspect :MasonLog")
  local mappings = require("mason-lspconfig.mappings").get_mason_map().lspconfig_to_package
  local packages = {}
  local versions = {}
  for _, identifier in ipairs(require("conf.tools").servers) do
    local name, version = identifier:match("^([^@]+)@(.+)$")
    local pkg = registry.get_package(assert(mappings[name], name))
    packages[#packages + 1] = pkg
    versions[pkg.name] = version
    if not pkg:is_installed() and not pkg:is_installing() then
      pkg:install({ version = version })
    end
  end
  assert(
    vim.wait(300000, function()
      for _, pkg in ipairs(packages) do
        if pkg:is_installing() or not pkg:is_installed() then
          return false
        end
      end
      return true
    end, 250),
    "Language-server installation failed or timed out; inspect :MasonLog"
  )
  for _, pkg in ipairs(packages) do
    assert(pkg:get_receipt():is_present(), "Missing installation receipt: " .. pkg.name)
    assert(
      pkg:get_installed_version() == versions[pkg.name],
      "Unexpected version for " .. pkg.name .. "; reinstall the pinned version via :Mason"
    )
    print("Installed " .. pkg.name)
  end
  require("nvim-treesitter").install(require("conf.tools").parsers):wait(300000)
  local installed = require("nvim-treesitter").get_installed("parsers")
  for _, lang in ipairs(require("conf.tools").parsers) do
    assert(vim.tbl_contains(installed, lang), "Missing parser: " .. lang)
  end
  print("All language servers and parsers installed")
end, debug.traceback)
if not ok then
  io.stderr:write(err .. "\n")
  vim.cmd("cquit 1")
end
vim.cmd("qa!")
