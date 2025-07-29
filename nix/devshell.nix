{
  perSystem = { config, pkgs, lib, self', ... }: {

    packages = {
      test = config.python-project.python.withPackages (ps: with ps; [ pytest ]);
      stdio = pkgs.writeShellApplication {
        name = "stdio";
        runtimeInputs = [ config.python-project.venv ];
        text = ''
          exec "${lib.getExe' self'.packages.default "python"}" ${config.python-project.root}/juspay_mcp/stdio.py "$@"
        '';
      };
    };

    apps = {
      default.program = "${lib.getExe' self'.packages.default "juspay-mcp"}";
      test.program = "${lib.getExe' self'.packages.test "pytest"}";
      stdio.program = "${lib.getExe' self'.packages.stdio "stdio"}";
    };


    devShells = {
      default = pkgs.mkShell {
        inputsFrom = [
          config.pre-commit.devShell
          config.devShells.uv2nix
        ];
      };
    };
  };
}
