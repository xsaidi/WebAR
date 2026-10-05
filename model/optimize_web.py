"""Non-destructive web export: simplify cushions, merge draw calls, portable normals."""
import bpy, math, os, importlib, json
OUT=r'C:\Users\saidix\Desktop\кроссплатформа курсач\forma-loft\dist\assets\models'
os.makedirs(OUT,exist_ok=True)
source=bpy.data.scenes['FORMA - Sofa Studio'];bpy.context.window.scene=source
collection=bpy.data.collections['FORMA 01 - Sofa']
fabric=bpy.data.materials['FORMA_Fabric']
thread=bpy.data.materials['FORMA_Seam_Thread']
fn=next(n for n in fabric.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
tn=next(n for n in thread.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
normalnode=next(n for n in fabric.node_tree.nodes if n.type=='NORMAL_MAP')
tex=next(n for n in fabric.node_tree.nodes if n.type=='TEX_IMAGE')
old_image=tex.image;old_strength=normalnode.inputs['Strength'].default_value
old_color=tuple(fn.inputs['Base Color'].default_value);old_thread=tuple(tn.inputs['Base Color'].default_value)
# USDZ conversion does not consistently carry normalScale. Bake it into pixels instead.
portable=bpy.data.images.new('FORMA Portable Weave',width=256,height=256)
portable.colorspace_settings.name='Non-Color'
pixels=list(old_image.pixels[:]);output=[]
for i in range(0,len(pixels),4):
    x=(pixels[i]*2-1)*old_strength;y=(pixels[i+1]*2-1)*old_strength
    z=math.sqrt(max(.01,1-x*x-y*y));output.extend((x*.5+.5,y*.5+.5,z*.5+.5,1))
portable.pixels.foreach_set(output);portable.pack()
tex.image=portable;normalnode.inputs['Strength'].default_value=1
dg=bpy.context.evaluated_depsgraph_get();copies=[]
for obj in collection.objects:
    if obj.type not in {'MESH','CURVE'}:continue
    saved=None
    if obj.type=='CURVE':saved=obj.data.bevel_resolution;obj.data.bevel_resolution=0;bpy.context.view_layer.update()
    mesh=bpy.data.meshes.new_from_object(obj.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg)
    copy=bpy.data.objects.new('Web_'+obj.name,mesh);copy.matrix_world=obj.matrix_world.copy();copies.append(copy)
    if saved is not None:obj.data.bevel_resolution=saved;bpy.context.view_layer.update()
temp=bpy.data.scenes.new('FORMA Web Export');bpy.context.window.scene=temp
try:
    for copy in copies:
        temp.collection.objects.link(copy)
        if 'Cushion' in copy.name and 'Piping' not in copy.name:
            modifier=copy.modifiers.new('Mobile geometry reduction','DECIMATE');modifier.ratio=.60
            bpy.context.view_layer.objects.active=copy;copy.select_set(True)
            bpy.ops.object.modifier_apply(modifier=modifier.name);copy.select_set(False)
    for copy in copies:copy.select_set(True)
    bpy.context.view_layer.objects.active=copies[0]
    bpy.ops.object.join();joined=bpy.context.view_layer.objects.active;joined.name='FORMA_Optimized'
    joined.data.calc_loop_triangles()
    print('Optimized triangles',len(joined.data.loop_triangles),'Material slots',len(joined.data.materials))
    formats=importlib.import_module('io_scene_gltf2').get_format_items(None,bpy.context)
    fmt=next(v[0] for v in formats if v[0].lower()=='glb')
    def col(hexstr):
        def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
        return tuple(linear(int(hexstr[i:i+2],16)/255) for i in (0,2,4))+(1,)
    palette={'terra':('AD6149','99533E'),'graphite':('535450','42433F'),'sand':('BBAA8E','96866E'),'olive':('71735B','585A44')}
    report=[]
    for key,(hexstr,seamhex) in palette.items():
        fn.inputs['Base Color'].default_value=col(hexstr);tn.inputs['Base Color'].default_value=col(seamhex)
        path=os.path.join(OUT,'sofa-'+key+'.glb')
        bpy.ops.export_scene.gltf(filepath=path,export_format=fmt,use_selection=True,use_active_scene=True)
        report.append({'variant':key,'bytes':os.path.getsize(path)})
    fn.inputs['Base Color'].default_value=old_color;tn.inputs['Base Color'].default_value=old_thread
    # Compare the optimized asset using the existing studio.
    for obj in bpy.data.collections['Studio - excluded from GLB'].objects:temp.collection.objects.link(obj)
    temp.world=source.world;temp.camera=source.camera
    temp.render.resolution_x=1200;temp.render.resolution_y=840;temp.render.resolution_percentage=100
    temp.render.filepath=r'C:\Users\saidix\Desktop\кроссплатформа курсач\forma-loft\model\optimized-preview.png'
    bpy.ops.render.render(write_still=True)
    print(json.dumps(report))
finally:
    tex.image=old_image;normalnode.inputs['Strength'].default_value=old_strength
    fn.inputs['Base Color'].default_value=old_color;tn.inputs['Base Color'].default_value=old_thread
    bpy.context.window.scene=source
    for obj in list(temp.objects):
        if obj.name.startswith('FORMA_Optimized') or obj.name.startswith('Web_'):
            mesh=obj.data;bpy.data.objects.remove(obj,do_unlink=True)
            if mesh.users==0:bpy.data.meshes.remove(mesh)
    bpy.data.scenes.remove(temp)
    bpy.data.images.remove(portable)
