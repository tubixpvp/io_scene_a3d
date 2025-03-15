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

from .IOTools import unpackStream, readNullTerminatedString, readLengthPrefixedString, calculatePadding

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
        self.name = readLengthPrefixedString(stream)
        self.color = unpackStream("<3f", stream)
        self.diffuseMap = readLengthPrefixedString(stream)

        print(f"[A3DMaterial name: {self.name} color: {self.color} diffuse map: {self.diffuseMap}]")

class A3DMesh:
    def __init__(self):
        self.name = ""
        self.bboxMax = None
        self.bboxMin = None
        self.vertexBuffers = []
        self.submeshes = []

        self.vertexCount = 0
        self.vertexBufferCount = 0
        self.submeshCount = 0

    def read2(self, stream):
        # Read vertex buffers
        self.vertexCount, self.vertexBufferCount = unpackStream("<2I", stream)
        print("unpacking vertex buffers, count=", self.vertexBufferCount)
        for _ in range(self.vertexBufferCount):
            vertexBuffer = A3DVertexBuffer()
            vertexBuffer.read2(self.vertexCount, stream)
            self.vertexBuffers.append(vertexBuffer)
        
        # Read submeshes
        self.submeshCount, = unpackStream("<I", stream)
        for _ in range(self.submeshCount):
            submesh = A3DSubmesh()
            submesh.read2(stream)
            self.submeshes.append(submesh)
        
        print(f"[A3DMesh name: {self.name} bbox max: {self.bboxMax} bbox min: {self.bboxMin} vertex buffers: {len(self.vertexBuffers)} submeshes: {len(self.submeshes)}]")
    
    def read3(self, stream):
        # Read mesh info
        self.name = readLengthPrefixedString(stream)
        # XXX: bbox order maybe incorrect, check this (might be min then max and not max then min)
        self.bboxMax = unpackStream("<3f", stream)
        self.bboxMin = unpackStream("<3f", stream)
        stream.read(4) # XXX: Unknown float value

        # Read vertex buffers
        self.vertexCount, self.vertexBufferCount = unpackStream("<2I", stream)
        for _ in range(self.vertexBufferCount):
            vertexBuffer = A3DVertexBuffer()
            vertexBuffer.read2(self.vertexCount, stream)
            self.vertexBuffers.append(vertexBuffer)
        
        # Read submeshes
        self.submeshCount, = unpackStream("<I", stream)
        for _ in range(self.submeshCount):
            submesh = A3DSubmesh()
            submesh.read3(stream)
            self.submeshes.append(submesh)
        
        print(f"[A3DMesh name: {self.name} bbox max: {self.bboxMax} bbox min: {self.bboxMin} vertex buffers: {len(self.vertexBuffers)} submeshes: {len(self.submeshes)}]")

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
        self.indices = []
        self.smoothingGroups = []
        self.materialID = None

        self.indexCount = 0

    def read2(self, stream):
        self.indexCount, = unpackStream("<I", stream) # This is just the face count so multiply it by 3
        self.indexCount *= 3
        self.indices = list(unpackStream(f"<{self.indexCount}H", stream))
        self.smoothingGroups = list(unpackStream(f"<{self.indexCount//3}I", stream))
        self.materialID, = unpackStream("<H", stream)

        if self.materialID == -1 or self.materialID == 65535:
            self.materialID = None

        print(f"[A3DSubmesh indices: {len(self.indices)} smoothing groups: {len(self.smoothingGroups)} materialID: {self.materialID}]")

    def read3(self, stream):
        # Read indices
        self.indexCount, = unpackStream("<I", stream)
        self.indices = list(unpackStream(f"<{self.indexCount}H", stream))
        
        # Padding
        padding = calculatePadding(self.indexCount*2) # Each index is 2 bytes
        stream.read(padding)

        print(f"[A3DSubmesh indices: {len(self.indices)} smoothing groups: {len(self.smoothingGroups)} materialID: {self.materialID}]")

class A3DTransform:
    def __init__(self):
        self.name = ""
        self.position = (0.0, 0.0, 0.0)
        self.rotation = (0.0, 0.0, 0.0, 0.0)
        self.scale = (0.0, 0.0, 0.0)

    def read2(self, stream):
        self.position = unpackStream("<3f", stream)
        self.rotation = unpackStream("<4f", stream)
        self.scale = unpackStream("<3f", stream)

        print(f"[A3DTransform position: {self.position} rotation: {self.rotation} scale: {self.scale}]")

    def read3(self, stream):
        self.name = readLengthPrefixedString(stream)
        self.position = unpackStream("<3f", stream)
        self.rotation = unpackStream("<4f", stream)
        self.scale = unpackStream("<3f", stream)

        print(f"[A3DTransform name: {self.name} position: {self.position} rotation: {self.rotation} scale: {self.scale}]")

class A3DObject:
    def __init__(self):
        self.name = ""
        self.meshID = None
        self.transformID = None
        self.materialIDs = []

        self.materialCount = 0

    def read2(self, stream):
        self.name = readNullTerminatedString(stream)
        self.meshID, self.transformID = unpackStream("<2I", stream)

        print(f"[A3DObject name: {self.name} meshID: {self.meshID} transformID: {self.transformID} materialIDs: {len(self.materialIDs)}]")

    def read3(self, stream):
        self.meshID, self.transformID, self.materialCount = unpackStream("<3I", stream)

        # Read material IDs
        for _ in range(self.materialCount):
            materialID, = unpackStream("<i", stream)
            self.materialIDs.append(materialID)

        print(f"[A3DObject name: {self.name} meshID: {self.meshID} transformID: {self.transformID} materialIDs: {len(self.materialIDs)}]")