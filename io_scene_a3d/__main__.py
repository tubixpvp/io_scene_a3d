from sys import argv
from .A3D import A3D

with open(argv[1], "rb") as f:
    model = A3D()
    model.read(f)