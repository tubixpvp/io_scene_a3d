import bmesh
import bpy
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper
from bpy_extras.node_shader_utils import PrincipledBSDFWrapper
from bpy_extras.image_utils import load_image

from .A3D import A3D
from .A3DObjects import (
    A3D_VERTEXTYPE_COORDINATE,
    A3D_VERTEXTYPE_UV1,
    A3D_VERTEXTYPE_NORMAL1,
    A3D_VERTEXTYPE_UV2,
    A3D_VERTEXTYPE_COLOR,
    A3D_VERTEXTYPE_NORMAL2
)

'''
Operators
'''
class ImportA3D(Operator, ImportHelper):
    bl_idname = "import_scene.alternativa"
    bl_label = "Import A3D"
    bl_description = "Import an A3D model"
    bl_options = {'PRESET', 'UNDO'}

    filter_glob: StringProperty(default="*.a3d", options={'HIDDEN'})

    # User options
    #try_import_textures: BoolProperty(name="Search for textures", description="Automatically search for lightmap, track and wheel textures and attempt to apply them", default=True)
    create_collection: BoolProperty(name="Create collection", description="Create a collection to hold all the model objects", default=True)

    def draw(self, context):
        import_panel_options(self.layout, self)

    def invoke(self, context, event):
        return ImportHelper.invoke(self, context, event)

    def execute(self, context):
        filepath = self.filepath
        
        # Read the file
        print(f"Reading A3D data from {filepath}")
        modelData = A3D()
        with open(filepath, "rb") as file:
            modelData.read(file)
        
        # Import data into blender
        print("Importing mesh data into blender")
        # Create materials
        materials = []
        for material in modelData.materials:
            ma = bpy.data.materials.new(material.name)
            maWrapper = PrincipledBSDFWrapper(ma, is_readonly=False, use_nodes=True)
            maWrapper.base_color = material.color
            maWrapper.roughness = 1.0

            materials.append(ma)
        # Build meshes
        meshes = []
        for mesh in modelData.meshes:
            me = bpy.data.meshes.new(mesh.name)

            # Gather all vertex data
            coordinates = []
            uv1 = []
            normal1 = []
            uv2 = []
            colors = []
            normal2 = []
            for vertexBuffer in mesh.vertexBuffers:
                if vertexBuffer.bufferType == A3D_VERTEXTYPE_COORDINATE:
                    coordinates += vertexBuffer.data
                elif vertexBuffer.bufferType == A3D_VERTEXTYPE_UV1:
                    uv1 += vertexBuffer.data
                elif vertexBuffer.bufferType == A3D_VERTEXTYPE_NORMAL1:
                    normal1 += vertexBuffer.data
                elif vertexBuffer.bufferType == A3D_VERTEXTYPE_UV2:
                    uv2 += vertexBuffer.data
                elif vertexBuffer.bufferType == A3D_VERTEXTYPE_COLOR:
                    colors += vertexBuffer.data
                elif vertexBuffer.bufferType == A3D_VERTEXTYPE_NORMAL2:
                    normal2 += vertexBuffer.data

            # Add blender vertices
            blenderVertexIndices = []
            blenderVertices = []
            blenderUV1s = []
            blenderUV2s = []
            for submesh in mesh.submeshes:
                polygonCount = len(submesh.indices) // 3
                me.vertices.add(polygonCount*3)
                me.loops.add(polygonCount*3)
                me.polygons.add(polygonCount)

                for indexI in range(submesh.indexCount):
                    index = submesh.indices[indexI]
                    blenderVertexIndices.append(indexI)
                    blenderVertices += list(coordinates[index])
                if len(uv1) != 0:
                    for indexI in range(submesh.indexCount):
                        index = submesh.indices[indexI]
                        x, y = uv1[index]
                        blenderUV1s.append((x, 1-y))
                if len(uv2) != 0:
                    for indexI in range(submesh.indexCount):
                        index = submesh.indices[indexI]
                        x, y = uv2[index]
                        blenderUV2s.append((x, 1-y))
            me.vertices.foreach_set("co", blenderVertices)
            me.polygons.foreach_set("loop_start", range(0, len(blenderVertices)//3, 3))
            me.loops.foreach_set("vertex_index", blenderVertexIndices)

            # UVs
            if len(uv1) != 0:
                uvData = me.uv_layers.new(name="UV1").data
                for polygonI, po in enumerate(me.polygons):
                    indexI = polygonI * 3
                    uvData[po.loop_start].uv = blenderUV1s[blenderVertexIndices[indexI]]
                    uvData[po.loop_start+1].uv = blenderUV1s[blenderVertexIndices[indexI+1]]
                    uvData[po.loop_start+2].uv = blenderUV1s[blenderVertexIndices[indexI+2]]
            if len(uv2) != 0:
                uvData = me.uv_layers.new(name="UV2").data
                for polygonI, po in enumerate(me.polygons):
                    indexI = polygonI * 3
                    uvData[po.loop_start].uv = blenderUV2s[blenderVertexIndices[indexI]]
                    uvData[po.loop_start+1].uv = blenderUV2s[blenderVertexIndices[indexI+1]]
                    uvData[po.loop_start+2].uv = blenderUV2s[blenderVertexIndices[indexI+2]]

            # Apply materials (version 2)
            faceIndexBase = 0
            for submeshI, submesh in enumerate(mesh.submeshes):
                if submesh.materialID == None:
                    continue
                me.materials.append(materials[submesh.materialID])
                for faceI in range(submesh.indexCount//3):
                    me.polygons[faceI+faceIndexBase].material_index = submeshI
                faceIndexBase += submesh.indexCount//3

            # Finalise
            me.validate()
            me.update()
            meshes.append(me)
        # Create objects
        collection = bpy.context.collection # By default use the active collection
        if self.create_collection:
            collection = bpy.data.collections.new("Object")
            bpy.context.collection.children.link(collection)
        for objec in modelData.objects:
            me = meshes[objec.meshID]
            mesh = modelData.meshes[objec.meshID]
            transform = modelData.transforms[objec.transformID]

            # Select a name for the blender object
            name = ""
            if objec.name != "":
                name = objec.name
            elif mesh.name != "":
                name = mesh.name
            else:
                name = transform.name

            # Create the object
            ob = bpy.data.objects.new(name, me)
            collection.objects.link(ob)

            # Set transform
            ob.location = transform.position
            ob.scale = transform.scale
            ob.rotation_mode = "QUATERNION"
            x, y, z, w = transform.rotation
            ob.rotation_quaternion = (w, x, y, z)

            # Apply materials (version 3)
            for materialID in objec.materialIDs:
                if materialID == -1:
                    continue
                me.materials.append(materials[materialID])
            # Set the default material to the first one we added
            for polygon in me.polygons:
                polygon.material_index = 0

        return {"FINISHED"}

'''
Menu
'''
def import_panel_options(layout, operator):
    header, body = layout.panel("alternativa_import_options", default_closed=False)
    header.label(text="Options")
    if body:
        #body.prop(operator, "try_import_textures")
        body.prop(operator, "create_collection")

def menu_func_import_a3d(self, context):
    self.layout.operator(ImportA3D.bl_idname, text="Alternativa3D HTML5 (.a3d)")

'''
Registration
'''
classes = [
    ImportA3D
]

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_a3d)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_a3d)

if __name__ == "__main__":
    register()