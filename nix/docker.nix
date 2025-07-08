{ inputs, ... }:
{
  perSystem = { pkgs, self', lib, ... }:
    let
      n2c = inputs.nix2container.packages.${pkgs.system}.nix2container;
      default = {
        name = "juspay-mcp";
        tag = "latest";
        config = {
          Env = [
            "PYTHONUNBUFFERED=1"
          ];
          Entrypoint = [ (lib.getExe' self'.packages.default "juspay-mcp") ];
        };
      };
      sse = default // {
        name = "juspay-mcp-sse";
        config = default.config // {
          ExposedPorts = {
            "8080/tcp" = { };
          };
        };
      };
      dashboard = default // {
        name = "juspay-dashboard-mcp";
        config = default.config // {
          Env = default.config.Env ++ [ "JUSPAY_MCP_TYPE=DASHBOARD" ];
          Entrypoint = [ (lib.getExe' self'.packages.stdio "stdio") ];
        };
      };
      dashboard-sse = dashboard // {
        name = "juspay-dashboard-mcp-sse";
        config = dashboard.config // {
          ExposedPorts = {
            "8080/tcp" = { };
          };
          Entrypoint = [ (lib.getExe' self'.packages.default "juspay-mcp") ];
        };
      };
    in
    {
      packages = {
        docker = n2c.buildImage default;
        docker-sse = n2c.buildImage sse;


        # Use `docker run -it <image-name:hash>`
        # For local running
        # Without `-it` flag the process will terminate instantly
        docker-dashboard = n2c.buildImage dashboard;
        docker-dashboard-sse = n2c.buildImage dashboard-sse;
      };
    };
}
