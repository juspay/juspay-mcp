default:
    @just --list

# Starts the MCP server
run:
  nix run

# Runs the stdio script
run-stdio:
  nix run .#stdio

# Runs the test suite
test:
  nix run .#test
