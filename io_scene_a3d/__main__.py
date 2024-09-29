'''
Copyright (C) 2024 Pyogenics <https://www.github.com/Pyogenics>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

from .A3DIOTools import unpackStream
from .A3D3_2 import A3D3_2
from .A3D3_3 import A3D3_3

def readA3D(file):
    signature = file.read(4)
    if signature != b"A3D\0":
        raise RuntimeError(f"Invalid A3D signature: {signature}")
    
    variant, _, rootBlockMarker, _ = unpackStream("<2H2I", file)
    if rootBlockMarker != 1:
        raise RuntimeError(f"Invalid root block marker: {rootBlockMarker}")
    
    if variant == 3:
        a3d = A3D3_3()
        a3d.read(file)
    elif variant == 2:
        a3d = A3D3_2()
        a3d.read(file)
    elif variant == 1:
        pass
    else:
        raise RuntimeError(f"Unknown A3D variant: {variant}")

from sys import argv
if __name__ == "__main__":
    with open(argv[1], "rb") as file:
        readA3D(file)