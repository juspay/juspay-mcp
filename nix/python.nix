{ inputs, ... }:
let
  inherit (inputs) uv2nix pyproject-nix pyproject-build-systems;
in
{
  perSystem = { self', config, pkgs, ... }:
    let
      inherit (pkgs) lib;
      root = ./../.;
      pythonVersionFile = "${root}/.python-version";

      versionStr =
        with builtins;
        with lib;
        let
          raw = if pathExists pythonVersionFile then readFile pythonVersionFile else "";
          m = match "([0-9]+)\\.([0-9]+).*" (removeSuffix "\n" raw); # ["3" "13"]
        in
        if m != null && m != [ ] then concatStringsSep "" m else "313";
      python = pkgs."python${versionStr}";
      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = root; };
      overlay = workspace.mkPyprojectOverlay { sourcePreference = "wheel"; };
      editableOverlay = workspace.mkEditablePyprojectOverlay { root = "$REPO_ROOT"; };

      pythonSet =
        (pkgs.callPackage pyproject-nix.build.packages {
          inherit python;
        }).overrideScope
          (
            lib.composeManyExtensions [
              pyproject-build-systems.overlays.default
              overlay
            ]
          );

      # reuquired to create editable venv
      editablePythonSet = pythonSet.overrideScope (
        lib.composeManyExtensions [
          editableOverlay
          (final: prev: {
            juspay-mcp = prev.juspay-mcp.overrideAttrs (old: {
              src = lib.fileset.toSource {
                root = old.src;
                fileset = lib.fileset.unions [
                  (old.src + "/pyproject.toml")
                  (old.src + "/README.md")
                  (old.src + "/juspay_mcp")
                  (old.src + "/juspay_dashboard_mcp")
                ];
              };
              nativeBuildInputs =
                old.nativeBuildInputs
                ++ final.resolveBuildSystem {
                  editables = [ ];
                };
            });
          })
        ]
      );
      venv = editablePythonSet.mkVirtualEnv "juspay-mcp" workspace.deps.all;
    in
    {
      packages.default = pythonSet.mkVirtualEnv "juspay-mcp" workspace.deps.all;
      packages.test = python.withPackages (ps: with ps; [ pytest ]);
      packages.stdio = pkgs.writeShellScriptBin "stdio" ''
        exec "${venv}/bib/python" ${inputs.self}/juspay-mcp/stdio.py "$@"
      '';
      devShells.default = self'.devShells.uv2nix;
      apps.default.program = "${self'.packages.default}/bin/juspay-mcp";
      apps.test.program = "${self'.packages.test}/bin/pytest";
      apps.stdio.program = "${self'.packages.stdio}/bin/stdio";

      devShells.uv2nix = pkgs.mkShell {
        inputsFrom = [
          config.pre-commit.devShell
        ];
        packages = [
          venv
          pkgs.uv
        ];
        env = {
          UV_NO_SYNC = "1";
          UV_PYTHON = "${venv}/bin/python";
          UV_PYTHON_DOWNLOADS = "never";
        };

        shellHook = # sh
          ''
            unset PYTHONPATH
            export REPO_ROOT="$(git rev-parse --show-toplevel)"
            export PYTHONPATH="$REPO_ROOT"
          '';
      };
    };
}
