{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python312
    python312Packages.virtualenv
    python312Packages.pip
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
      python3.12 -m venv .venv
    fi

    source .venv/bin/activate

    echo "🚀 Entorno listo para AgeCare Core API (NixOS / nix-shell)"
    echo "   • Servidor local:  uvicorn app.main:app --reload --port 8000"
    echo "   • Pruebas:         pytest"
    echo "   • Contenedores:    podman-compose up --build"
  '';
}
