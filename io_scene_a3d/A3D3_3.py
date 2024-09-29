'''
Copyright (C) 2024 Pyogenics <https://www.github.com/Pyogenics>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

from .A3DIOTools import unpackStream, readString, calculatePadding
from .A3D3Shared import A3D3Mesh, A3D3Submesh, A3D3Transform

'''
A3D version 3 type 3
'''
class A3D3_3:
    def __init__(self):
        self.materials = {}
        self.materialNames = []
        self.meshes = []
        self.transforms = []

    def readSubmesh(self, stream):
        print("Reading submesh")

        indexCount, = unpackStream("<I", stream)
        faces = []
        for _ in range(indexCount//3):
            face = unpackStream("<3H", stream)
            faces.append(face)

        paddingSize = calculatePadding(indexCount*2)
        stream.read(paddingSize)

        submesh = A3D3Submesh(faces, [], 0) # XXX: Maybe this should be `None` instead of 0?
        return submesh

    def readVertices(self, vertexCount, floatCount, stream):
        vertices = []
        for _ in range(vertexCount):
            vertex = unpackStream(f"{floatCount}f", stream)
            vertices.append(vertex)
        return vertices

    def readMaterialBlock(self, stream):
        print("Reading material block")
        marker, _, materialCount = unpackStream("<3I", stream)
        if marker != 4:
            raise RuntimeError(f"Invalid material block marker: {marker}")

        for _ in range(materialCount):
            materialName = readString(stream)
            floats = unpackStream("<3f", stream)

            diffuseMap = readString(stream)
            print(f"{materialName} {floats} {diffuseMap}")

            self.materialNames.append(materialName)
            self.materials[materialName] = diffuseMap

    def readMeshBlock(self, stream):
        print("Reading mesh block")
        marker, _, meshCount = unpackStream("<3I", stream)
        if marker != 2:
            raise RuntimeError(f"Invalid mesh block marker: {marker}")

        for meshI in range(meshCount):
            print(f"Reading mesh {meshI} @ {stream.tell()}")

            # Vertices
            coordinates = []
            uv1 = []
            normals = []
            uv2 = []
            colors = []
            unknown = []

            submeshes = []

            meshName = readString(stream)
            unknownFloats = unpackStream("7f", stream)
            print(f"{meshName} {unknownFloats}")

            # Read vertex buffers
            vertexCount, vertexBufferCount = unpackStream("<2I", stream)
            for vertexBufferI in range(vertexBufferCount):
                print(f"Reading vertex buffer {vertexBufferI} with {vertexCount} vertices")

                bufferType, = unpackStream("<I", stream)
                if bufferType == 1:
                    coordinates = self.readVertices(vertexCount, 3, stream)
                elif bufferType == 2:
                    uv1 = self.readVertices(vertexCount, 2, stream)
                elif bufferType == 3:
                    normals = self.readVertices(vertexCount, 3, stream)
                elif bufferType == 4:
                    uv2 = self.readVertices(vertexCount, 2, stream)
                elif bufferType == 5:
                    colors = self.readVertices(vertexCount, 4, stream)
                elif bufferType == 6:
                    unknown = self.readVertices(vertexCount, 3, stream)
                else:
                    raise RuntimeError(f"Unknown vertex buffer type {bufferType}")

            # Read submeshes
            submeshCount, = unpackStream("<I", stream)
            for _ in range(submeshCount):
                submesh = self.readSubmesh(stream)
                submeshes.append(submesh)
            
            mesh = A3D3Mesh(coordinates, uv1, normals, uv2, colors, unknown, submeshes)
            mesh.faces += submesh.faces
            self.meshes.append(mesh)

    def readTransformBlock(self, stream):
        print("Reading transform block")
        marker, _, transformCount = unpackStream("<3I", stream)
        if marker != 3:
            raise RuntimeError(f"Invalid transform block marker: {marker}")

        for _ in range(transformCount):
            name = readString(stream)
            position = unpackStream("<3f", stream)
            rotation = unpackStream("<4f", stream)
            scale = unpackStream("<3f", stream)

            print(f"{name} {position} {rotation} {scale}")
            transform = A3D3Transform(position, rotation, scale, name)
            self.transforms.append(transform)
        for transformI in range(transformCount):
            transformID, = unpackStream("<I", stream)
            self.transforms[transformI].id = transformID

    # Heirarchy data
    def readObjectBlock(self, stream):
        print("Reading object block")
        marker, _, objectCount = unpackStream("<3I", stream)
        if marker != 5:
            raise RuntimeError(f"Invalid object block marker: {marker}")

        for _ in range(objectCount):
            meshID, transformID, materialCount = unpackStream("<3I", stream)
            for materialI in range(materialCount):
                materialID, = unpackStream("<i", stream)
                if materialID >= 0:
                    self.meshes[meshID].submeshes[materialI].material = self.materialNames[materialID]
            
            self.meshes[meshID].transform = self.transforms[transformID]

    def read(self, stream):
        print("Reading A3D3 type 3")

        self.readMaterialBlock(stream)
        self.readMeshBlock(stream)
        self.readTransformBlock(stream)
        self.readObjectBlock(stream)