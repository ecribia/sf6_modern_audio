{
  description = "devShell for modern";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-25.05";
  };

  outputs = {
    self,
    nixpkgs,
  }: let
    pkgs = nixpkgs.legacyPackages."x86_64-linux";
  in {
    devShells."x86_64-linux".default = pkgs.mkShell {
      packages = let
        py = pkgs.python313Packages;
      in
        with pkgs; [
          python313
          py.opencv-python
          py.numpy
          py.mss
          py.pygame
          py.pillow
          grim
        ];
    };
  };
}
