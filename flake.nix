{
  description = "AgeCare Core API Backend - Nix Development Environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python312;
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python
            python.pkgs.virtualenv
            python.pkgs.pip
            stdenv.cc.cc.lib
            zlib
            openssl
            postgresql
            podman-compose
            docker-compose
          ];

          shellHook = ''
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.zlib}/lib:$LD_LIBRARY_PATH"
            export PYTHONPATH=".:$PYTHONPATH"

            if [ ! -d ".venv" ]; then
              echo "📦 Creando venv en .venv..."
              ${python}/bin/python -m venv .venv
            fi

            source .venv/bin/activate

            echo "🚀 Entorno listo para AgeCare Core API (NixOS)"
            echo "   • Servidor local:  uvicorn app.main:app --reload --port 8000"
            echo "   • Pruebas:         pytest"
            echo "   • Contenedores:    podman-compose up --build"
          '';
        };
      }
    );
}
