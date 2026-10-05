"""Export only the sofa, with evaluated bevels and seams, in four upholstery colors."""
import bpy, os, math, json, importlib
from mathutils import Vector
OUT=r'C:\Users\saidix\Desktop\кроссплатформа курсач\forma-loft\model'
source_scene=bpy.context.scene
source_collection=bpy.data.collections['FORMA 01 - Sofa']
fabric=bpy.data.materials['FORMA_Fabric']
thread=bpy.data.materials['FORMA_Seam_Thread']
bsdf=next(n for n in fabric.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
threadnode=next(n for n in thread.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
original_color=tuple(bsdf.inputs['Base Color'].default_value)
original_thread=tuple(threadnode.inputs['Base Color'].default_value)
depsgraph=bpy.context.evaluated_depsgraph_get()
copies=[]
for obj in source_collection.objects:
    if obj.type in {'MESH','CURVE'}:
        mesh=bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph),preserve_all_data_layers=True,depsgraph=depsgraph)
        copy=bpy.data.objects.new(obj.name,mesh);copy.matrix_world=obj.matrix_world.copy();copies.append(copy)
export_scene=bpy.data.scenes.new('FORMA Export Temporary')
bpy.context.window.scene=export_scene
root=bpy.data.objects.new('FORMA_01',None);export_scene.collection.objects.link(root)
for obj in copies:export_scene.collection.objects.link(obj);obj.parent=root;obj.select_set(True)
root.select_set(True)
bpy.context.view_layer.objects.active=root
formats=[i.identifier for i in bpy.ops.export_scene.gltf.get_rna_type().properties['export_format'].enum_items]
if not formats:
    formats=[item[0] for item in importlib.import_module('io_scene_gltf2').get_format_items(None,bpy.context)]
fmt=next(i for i in formats if i.lower()=='glb')
palette={'terra':('AD6149','99533E'),'graphite':('535450','42433F'),'sand':('BBAA8E','96866E'),'olive':('71735B','585A44')}
def color(hexstr):
    def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
    return tuple(linear(int(hexstr[i:i+2],16)/255) for i in (0,2,4))+(1,)
results=[]
try:
    for variant,(hexstr,seamhex) in palette.items():
        bsdf.inputs['Base Color'].default_value=color(hexstr)
        threadnode.inputs['Base Color'].default_value=color(seamhex)
        filename='forma-sofa.glb' if variant=='terra' else 'forma-sofa-'+variant+'.glb'
        path=os.path.join(OUT,filename)
        bpy.ops.export_scene.gltf(filepath=path,export_format=fmt,use_selection=True,use_active_scene=True,export_apply=False)
        results.append({'color':variant,'file':filename,'bytes':os.path.getsize(path)})
finally:
    bsdf.inputs['Base Color'].default_value=original_color;threadnode.inputs['Base Color'].default_value=original_thread
    bpy.context.window.scene=source_scene
    for obj in copies:
        mesh=obj.data;bpy.data.objects.remove(obj,do_unlink=True);bpy.data.meshes.remove(mesh)
    bpy.data.objects.remove(root,do_unlink=True);bpy.data.scenes.remove(export_scene)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'forma-sofa.blend'))
print(json.dumps(results))
