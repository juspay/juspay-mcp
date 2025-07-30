{ inputs, ... }:
{
  imports = [ inputs.python-flake.flakeModules.default ];
  perSystem = { ... }:
    {
      python-project = {
        name = "juspay-mcp";
        pythonVersionFile = true;
        root = ../.;
      };
    };
}
