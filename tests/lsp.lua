-- End-to-end requests against real language servers using disposable projects.
local fixtures = {
  { "ts_ls", "sample.ts", { "const value = 'hello';", "console.log(value);", "missing_name;" }, 1 },
  { "pyright", "sample.py", { "value = 'hello'", "print(value)", "missing_name" }, 1 },
  {
    "clangd",
    "sample.c",
    { "int value = 1;", "int main(void) { return value + missing_name; }" },
    1,
  },
  { "lua_ls", "sample.lua", { "local value = 'hello'", "print(value)", "missing_name()" }, 1 },
  { "html", "sample.html", { '<div id="value">hello</div>', "<di" }, 1, 3 },
  { "cssls", "sample.css", { ".value { color: red; }", "a { col }" }, 1, 7 },
  {
    "jdtls",
    "Sample.java",
    {
      "public class Sample {",
      '  static String value = "hello";',
      "  static String run() { return value + missing_name; }",
      "}",
    },
    2,
  },
}

local tmp = vim.fn.tempname()
-- Exercise two distinct Java roots with the same final directory name.
fixtures[#fixtures + 1] = vim.deepcopy(fixtures[#fixtures])
local clients = {}
local ok, err = xpcall(function()
  for index, case in ipairs(fixtures) do
    if not vim.env.NVIM_TEST_SERVER or vim.env.NVIM_TEST_SERVER == case[1] then
      local server, filename, lines, row = unpack(case)
      local root = tmp .. "/" .. index .. "/project"
      vim.fn.mkdir(root .. "/.git", "p")
      vim.fn.writefile({ '{"name":"nvim-config-smoke","private":true}' }, root .. "/package.json")
      if server == "jdtls" then
        vim.fn.writefile({
          '<project xmlns="http://maven.apache.org/POM/4.0.0"><modelVersion>4.0.0</modelVersion>',
          "<groupId>smoke</groupId><artifactId>smoke</artifactId><version>1</version>",
          "<properties><maven.compiler.release>21</maven.compiler.release></properties></project>",
        }, root .. "/pom.xml")
        filename = "src/main/java/" .. filename
        vim.fn.mkdir(root .. "/src/main/java", "p")
      end
      local path = root .. "/" .. filename
      vim.fn.writefile(lines, path)
      vim.cmd.edit(vim.fn.fnameescape(path))
      local buf = vim.api.nvim_get_current_buf()
      local client
      assert(
        vim.wait(120000, function()
          client = vim.lsp.get_clients({ bufnr = buf, name = server })[1]
          return client and client.initialized
        end, 100),
        server .. " failed to initialize"
      )
      clients[#clients + 1] = client
      local col = case[5] or (assert(lines[row + 1]:find("value", 1, true)) - 1)
      local params = {
        textDocument = { uri = vim.uri_from_bufnr(buf) },
        position = { line = row, character = col + (case[5] and 0 or 2) },
      }
      if server ~= "html" then
        assert(
          vim.wait(60000, function()
            return #vim.diagnostic.get(buf) > 0
          end, 100),
          server .. " returned no diagnostics"
        )
      end
      local response = client:request_sync("textDocument/completion", params, 60000, buf)
      assert(
        response and not response.err,
        server .. " completion request failed: " .. vim.inspect(response)
      )
      local items = response.result and (response.result.items or response.result)
      assert(type(items) == "table" and #items > 0, server .. " returned no completion items")
      if server ~= "html" and server ~= "cssls" then
        local definition = client:request_sync("textDocument/definition", params, 60000, buf)
        assert(
          definition
            and not definition.err
            and definition.result
            and not vim.tbl_isempty(definition.result),
          server .. " returned no definition"
        )
        local hover = client:request_sync("textDocument/hover", params, 60000, buf)
        assert(hover and not hover.err and hover.result, server .. " returned no hover information")
      end
      print(server .. ": completion, navigation where supported, and diagnostics passed")
      client:stop()
      assert(vim.wait(10000, function()
        return client:is_stopped()
      end, 50))
      vim.cmd("bwipeout!")
    end
  end
end, debug.traceback)
for _, client in ipairs(clients) do
  client:stop(true)
end
vim.fn.delete(tmp, "rf")
if not ok then
  io.stderr:write(err .. "\n")
  vim.cmd("cquit 1")
end
vim.cmd("qa!")
