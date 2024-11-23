'''
Copyright (c) 2024 Pyogenics <https://github.com/Pyogenics>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

from .IOTools import unpackStream, readNullTerminatedString

class A3DMaterial:
    def __init__(self):
        self.name = ""
        self.color = (0.0, 0.0, 0.0)
        self.diffuseMap = ""
    
    def read2(self, stream):
        self.name = readNullTerminatedString(stream)
        self.color = unpackStream("<3f", stream)
        self.diffuseMap = readNullTerminatedString(stream)

        print(f"[A3DMaterial name: {self.name} color: {self.color} diffuse map: {self.diffuseMap}]")

    def read3(self, stream):
        pass

class A3DMesh:
    def __init__(self):
        self.vertexBuffers = []
        self.submeshes = []

    def read2(self, stream):
        # Read vertex buffers
        vertexCount, bufferCount = unpackStream("<2I", stream)
        for _ in range(bufferCount):
            vertexBuffer = A3DVertexBuffer()
            vertexBuffer.read2(vertexCount, stream)
            self.vertexBuffers.append(vertexBuffer)
        
        # Read submeshes
        submeshCount, = unpackStream("<I", stream)
        for _ in range(submeshCount):
            submesh = A3DSubmesh()
            submesh.read2(stream)
            self.submeshes.append(submesh)
        
        print(f"[A3DMesh vertex buffers: {len(self.vertexBuffers)} submeshes: {len(self.submeshes)}]")

A3D_VERTEXTYPE_COORDINATE = 1
A3D_VERTEXTYPE_UV1 = 2
A3D_VERTEXTYPE_NORMAL1 = 3
A3D_VERTEXTYPE_UV2 = 4
A3D_VERTEXTYPE_COLOR = 5
A3D_VERTEXTYPE_NORMAL2 = 6
# LUT for vertex buffer types -> vertex size
A3DVertexSize = {
    A3D_VERTEXTYPE_COORDINATE: 3,
    A3D_VERTEXTYPE_UV1: 2,
    A3D_VERTEXTYPE_NORMAL1: 3,
    A3D_VERTEXTYPE_UV2: 2,
    A3D_VERTEXTYPE_COLOR: 4,
    A3D_VERTEXTYPE_NORMAL2: 3
}
class A3DVertexBuffer:
    def __init__(self):
        self.data = []
        self.bufferType = None

    def read2(self, vertexCount, stream):
        self.bufferType, = unpackStream("<I", stream)
        if not (self.bufferType in A3DVertexSize.keys()):
            raise RuntimeError(f"Unknown vertex buffer type: {self.bufferType}")
        for _ in range(vertexCount):
            vertexSize = A3DVertexSize[self.bufferType]
            vertex = unpackStream(f"<{vertexSize}f", stream)
            self.data.append(vertex)
        
        print(f"[A3DVertexBuffer data: {len(self.data)} buffer type: {self.bufferType}]")

class A3DSubmesh:
    def __init__(self):
        self.faces = []
        self.smoothingGroups = []
        self.materialID = None

    def read2(self, stream):
        faceCount, = unpackStream("<I", stream)
        for _ in range(faceCount):
            face = unpackStream("<3H", stream)
            self.faces.append(face)
        for _ in range(faceCount):
            smoothingGroup, = unpackStream("<I", stream)
            self.smoothingGroups.append(smoothingGroup)
        self.materialID, = unpackStream("<H", stream)

        print(f"[A3DSubmesh faces: {len(self.faces)} smoothing groups: {len(self.smoothingGroups)} materialID: {self.materialID}]")

class A3DTransform:
    def __init__(self):
        self.position = (0.0, 0.0, 0.0)
        self.rotation = (0.0, 0.0, 0.0, 0.0)
        self.scale = (0.0, 0.0, 0.0)

    def read2(self, stream):
        self.position = unpackStream("<3f", stream)
        self.rotation = unpackStream("<4f", stream)
        self.scale = unpackStream("<3f", stream)

        print(f"[A3DTransform position: {self.position} rotation: {self.rotation} scale: {self.scale}]")

class A3DObject:
    def __init__(self):
        self.name = ""
        self.meshID = None
        self.transformID = None

    def read2(self, stream):
        self.name = readNullTerminatedString(stream)
        self.meshID, self.transformID = unpackStream("<2I", stream)

        print(f"[A3DObject name: {self.name} meshID: {self.meshID} transformID: {self.transformID}]")
