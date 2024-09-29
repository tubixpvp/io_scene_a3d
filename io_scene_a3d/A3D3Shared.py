'''
Copyright (C) 2024 Pyogenics <https://www.github.com/Pyogenics>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

class A3D3Mesh:
    def __init__(self, coordinates, uv1, normals, uv2, colors, unknown, submeshes):
        # Vertex data
        self.coordinates = coordinates
        self.uv1 = uv1
        self.normals = normals
        self.uv2 = uv2
        self.colors = colors
        self.unknown = unknown

        self.submeshes = submeshes
        self.faces = [] # Aggregate of all submesh face data, easier for blender importing

        # Object data
        self.name = ""
        self.transform = None

class A3D3Submesh:
    def __init__(self, faces, smoothingGroups, material):
        self.faces = faces
        self.smoothingGroups = smoothingGroups
        self.material = material

class A3D3Transform:
    def __init__(self, position, rotation, scale, name):
        self.position = position
        self.rotation = rotation
        self.scale = scale
        self.name = name
        self.parentID = 0