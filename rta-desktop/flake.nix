{
  description = "RTA Desktop - AI-powered IDE";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            nodejs_20
            yarn
            python3
            gcc
            pkg-config
            xorg.libX11
            xorg.libX11.dev
            xorg.libxkbfile
            libxkbcommon
          ];

          shellHook = ''
            echo "🛠️  RTA Desktop development environment"
            echo "Node: $(node --version)"
            echo "Yarn: $(yarn --version)"
          '';
        };
      });
}
