'''
Copyright (C) 2024 Pyogenics <https://www.github.com/Pyogenics>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

bl_info = {
    "name": "Modern A3D",
    "description": "Support for modern a3d models",
    "author": "Pyogenics, https://www.github.com/Pyogenics",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "File > Import-Export",
    "category": "Import-Export"
}

import bmesh
import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from .A3D3_2 import A3D3_2
from .A3D3_3 import A3D3_3
from .A3DIOTools import unpackStream

'''
Operators
'''
class ImportA3DModern(Operator, ImportHelper):
    bl_idname = "import_scene.a3dmodern"
    bl_label = "Import A3D"
    bl_description = "Import an A3D model"

    filter_glob: StringProperty(default="*.a3d", options={'HIDDEN'})

    def invoke(self, context, event):
        return ImportHelper.invoke(self, context, event)

    def execute(self, context):
        filepath = self.filepath
        print(f"Importing A3D scene from {filepath}")
        
        with open(filepath, "rb") as file:
            signature = file.read(4)
            if signature != b"A3D\0":
                raise RuntimeError(f"Invalid A3D signature: {signature}")
            
            variant, _, rootBlockMarker, _ = unpackStream("<2H2I", file)
            if rootBlockMarker != 1:
                raise RuntimeError(f"Invalid root block marker: {rootBlockMarker}")
            
            if variant == 3:
                a3d = A3D3_3()
                a3d.read(file)

                for mesh in a3d.meshes:
                    blenderMesh = self.createBlenderMeshMin(mesh)
                    blenderObject = bpy.data.objects.new(mesh.name, blenderMesh)
                    bpy.context.collection.objects.link(blenderObject)
            elif variant == 2:
                a3d = A3D3_2()
                a3d.read(file)

                # Create our materials
                materials = {}
                for materialName in a3d.materialNames:
                    materials[materialName] = bpy.data.materials.new(materialName)

                a3dMesh = a3d.meshes[0]
                blenderMesh = self.createBlenderMesh(a3dMesh, materials)
                blenderObject = bpy.data.objects.new(a3dMesh.name, blenderMesh)
                bpy.context.collection.objects.link(blenderObject)
            elif variant == 1:
                pass
            else:
                pass

            self.report({"INFO"}, f"Loaded A3D")

        return {"FINISHED"}

    def createBlenderMeshMin(self, mesh):
        me = bpy.data.meshes.new(mesh.name)
        bm = bmesh.new()

        for coord in mesh.coordinates:
            bm.verts.new(coord)
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()
        for face in mesh.faces:
            v1, v2, v3 = face
            bm.faces.new([
                bm.verts[v1],
                bm.verts[v2],
                bm.verts[v3]
            ])

        layers = []
        if len(mesh.uv1) != 0:
            layers.append(
                (bm.loops.layers.uv.new("UV1"), mesh.uv1)
            )
            print("has UV1")
        if len(mesh.uv2) != 0:
            layers.append(
                (bm.loops.layers.uv.new("UV2"), mesh.uv2)
            )
            print("has UV2")
        for face in bm.faces:
            for loop in face.loops:
                for uvLayer, uvData in layers: loop[uvLayer].uv = uvData[loop.vert.index]
                loop.vert.normal = mesh.normals[loop.vert.index]

        bm.to_mesh(me)
        me.update()

        return me

    def createBlenderMesh(self, mesh, materials):
        me = bpy.data.meshes.new(mesh.name)
        bm = bmesh.new()

        for coord in mesh.coordinates:
            bm.verts.new(coord)
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()
        for face in mesh.faces:
            v1, v2, v3 = face
            bm.faces.new([
                bm.verts[v1],
                bm.verts[v2],
                bm.verts[v3]
            ])

        layers = []
        if len(mesh.uv1) != 0:
            layers.append(
                (bm.loops.layers.uv.new("UV1"), mesh.uv1)
            )
            print("has UV1")
        if len(mesh.uv2) != 0:
            layers.append(
                (bm.loops.layers.uv.new("UV2"), mesh.uv2)
            )
            print("has UV2")
        for face in bm.faces:
            for loop in face.loops:
                for uvLayer, uvData in layers: loop[uvLayer].uv = uvData[loop.vert.index]
                loop.vert.normal = mesh.normals[loop.vert.index]

        bm.to_mesh(me)
        me.update()

        # Materials
        for submesh in mesh.submeshes:
            material = materials[submesh.material]
            me.materials.append(material)
            materialI = len(me.materials) - 1
            for polygon in me.polygons:
                polygon.material_index = materialI

        return me

'''
Menu
'''
def menu_func_import_a3d(self, context):
    self.layout.operator(ImportA3DModern.bl_idname, text="A3D Modern")

'''
Register
'''
classes = {
    ImportA3DModern
}

def register():
    # Register classes
    for c in classes:
        bpy.utils.register_class(c)
    # File > Import-Export
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_a3d)
#    bpy.types.TOPBAR_MT_file_export.append(menu_func_export_dava)

def unregister():
    # Unregister classes
    for c in classes:
        bpy.utils.unregister_class(c)
    # Remove `File > Import-Export`
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_a3d)
#    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export_dava)