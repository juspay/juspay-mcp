{
  description = "Flake for Juspay-mcp python project.";

  inputs = {
    flake-parts.url = "github:hercules-ci/flake-parts";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    systems.url = "github:nix-systems/default";

    git-hooks.url = "github:cachix/git-hooks.nix";
    git-hooks.flake = false;

    nix2container.url = "github:nlewo/nix2container";

    # TODO: update once the PR is merged
    python-flake.url = "github:juspay/python-flake/pull/2/head";
  };

  outputs = inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      debug = true;
      systems = import inputs.systems;
      imports = with builtins; map (fn: ./nix/${fn}) (attrNames (readDir ./nix));
    };
}
