{ inputs, ... }:
{
  perSystem = { pkgs, self', lib, ... }:
    let
      n2c = inputs.nix2container.packages.${pkgs.system}.nix2container;
    in
    {
      packages = {
        docker = n2c.buildImage {
          name = "juspay-mcp";
          tag = "latest";
          config = {
            Env = [
              "PYTHONUNBUFFERED=1"
            ];
            Entrypoint = [ "${lib.getExe' self'.packages.default "juspay-mcp"}" ];
          };
        };
        # Use `docker run -it <image-name:hash>`
        # For local running
        # Without `-it` flag the process will terminate instantly
        docker-dashboard = n2c.buildImage {
          name = "juspay-dashboard-mcp";
          tag = "latest";
          config = {
            Env = [
              "PYTHONUNBUFFERED=1"
              "JUSPAY_MCP_TYPE=DASHBOARD"
            ];
            Entrypoint = [ "${lib.getExe' self'.packages.stdio "stdio"}" ];
          };
        };
      };
    };
}
