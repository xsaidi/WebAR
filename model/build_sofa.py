"""Editable FORMA sofa built from the user's four image references. Metres."""
import bpy, bmesh, math, os
from mathutils import Vector

OUT = r'C:\Users\saidix\Desktop\кроссплатформа курсач\forma-loft\model'
os.makedirs(OUT, exist_ok=True)
scene = bpy.data.scenes.new('FORMA - Sofa Studio')
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
sofa = bpy.data.collections.new('FORMA 01 - Sofa')
studio = bpy.data.collections.new('Studio - excluded from GLB')
scene.collection.children.link(sofa)
scene.collection.children.link(studio)
root = bpy.data.objects.new('FORMA_01', None)
sofa.objects.link(root)
root['dimensions_m'] = '2.20 x 0.96 x approximately 0.98'
root['reference'] = 'Four user-generated terracotta sofa views; dimensions inferred.'
root['fabric_material'] = 'FORMA_Fabric'

def linear(v):
    return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
def rgb(hexstr):
    return tuple(linear(int(hexstr[i:i+2],16)/255) for i in (0,2,4)) + (1,)
def material(name, color, roughness, metallic=0):
    mat = bpy.data.materials.new(name)
    node = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    node.inputs['Base Color'].default_value = rgb(color)
    node.inputs['Roughness'].default_value = roughness
    node.inputs['Metallic'].default_value = metallic
    mat.diffuse_color = rgb(color)
    return mat, node
fabric, bsdf = material('FORMA_Fabric', 'AD6149', .87)
sock = bsdf.inputs.get('Sheen Weight')
if sock: sock.default_value = .22
steel, _ = material('FORMA_Black_Powder_Coated_Steel', '292C2C', .4, .65)
thread, _ = material('FORMA_Seam_Thread', '99533E', .92)
floor_mat, _ = material('Studio Warm Stone', 'D3D0C8', .8)

# A packed tangent-space weave normal map is portable to GLB.
size = 256
normal = bpy.data.images.new('FORMA_Weave_Normal', width=size, height=size)
normal.colorspace_settings.name = 'Non-Color'
pixels = []
for y in range(size):
    for x in range(size):
        u = 2*math.pi*x/8
        v = 2*math.pi*y/8
        nx = .18*math.cos(u)*( .65+.35*math.sin(v))
        ny = .18*math.cos(v)*( .65+.35*math.sin(u))
        nz = math.sqrt(max(.01,1-nx*nx-ny*ny))
        pixels.extend((nx*.5+.5,ny*.5+.5,nz*.5+.5,1))
normal.pixels.foreach_set(pixels)
normal.filepath_raw = os.path.join(OUT,'fabric_normal.png')
formats = [i.identifier for i in normal.bl_rna.properties['file_format'].enum_items]
normal.file_format = next(f for f in formats if f.lower()=='png')
normal.save(); normal.pack()
nodes = fabric.node_tree.nodes; links = fabric.node_tree.links
tex = nodes.new('ShaderNodeTexImage'); tex.image = normal
uv = nodes.new('ShaderNodeUVMap'); uv.uv_map = 'FabricUV'
normalnode = nodes.new('ShaderNodeNormalMap'); normalnode.inputs['Strength'].default_value=.28
links.new(uv.outputs['UV'],tex.inputs['Vector'])
links.new(tex.outputs['Color'],normalnode.inputs['Color'])
links.new(normalnode.outputs['Normal'],bsdf.inputs['Normal'])

def uv_map(obj):
    uv = obj.data.uv_layers.new(name='FabricUV')
    # Planar per-face mapping in physical metres, repeating every 0.12 m.
    for polygon in obj.data.polygons:
        axis = max(range(3),key=lambda i:abs(polygon.normal[i]))
        axes = [i for i in range(3) if i != axis]
        for li in polygon.loop_indices:
            p = obj.data.vertices[obj.data.loops[li].vertex_index].co
            uv.data[li].uv = (p[axes[0]]/.12,p[axes[1]]/.12)

def rounded(name, dims, loc, radius, mat, segments=5, collection=sofa):
    hx,hy,hz = [d/2 for d in dims]
    vertices = [(x*hx,y*hy,z*hz) for x,y,z in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
    faces = [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
    mesh=bpy.data.meshes.new(name+'_Mesh');mesh.from_pydata(vertices,[],faces);mesh.update()
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();mesh.update()
    obj=bpy.data.objects.new(name,mesh);collection.objects.link(obj);obj.location=loc
    if collection==sofa: obj.parent=root
    obj.data.materials.append(mat)
    bevel=obj.modifiers.new('Soft tailored edges','BEVEL');bevel.width=radius;bevel.segments=segments
    weighted=obj.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL');weighted.keep_sharp=True
    for p in mesh.polygons:p.use_smooth=True
    uv_map(obj)
    return obj

def pillow_surface(p,half,r,axis,sign,bulge):
    core=Vector([max(-half[i]+r,min(half[i]-r,p[i])) for i in range(3)])
    delta=Vector(p)-core
    result=core + delta.normalized()*r if delta.length else core
    tangents=[i for i in range(3) if i!=axis]
    fade=math.prod(max(0,math.cos(math.pi*.5*p[i]/half[i])) for i in tangents)
    result[axis]+=sign*bulge*fade
    # Very subtle broad upholstered unevenness, strongest on the lower backrest face.
    if axis==1 and sign==-1:
        x,z=p[0]/half[0],p[2]/half[2]
        result[axis]-=.0025*math.sin(x*24+.4)*math.exp(-((z+.55)/.24)**2)*fade
    return result

def pillow(name,dims,loc,r,rotation=0,bulge=.014):
    half=[d/2 for d in dims];steps=16;verts=[];faces=[]
    for axis in range(3):
        tangents=[i for i in range(3) if i!=axis]
        for sign in [-1,1]:
            start=len(verts)
            for a in range(steps+1):
                for b in range(steps+1):
                    p=[0.,0.,0.];p[axis]=sign*half[axis]
                    p[tangents[0]]=half[tangents[0]]*(2*a/steps-1)
                    p[tangents[1]]=half[tangents[1]]*(2*b/steps-1)
                    verts.append(pillow_surface(p,half,r,axis,sign,bulge))
            for a in range(steps):
                for b in range(steps):
                    q=start+a*(steps+1)+b
                    faces.append((q,q+steps+1,q+steps+2,q+1))
    mesh=bpy.data.meshes.new(name+'_Mesh');mesh.from_pydata(verts,[],faces);mesh.update()
    bm=bmesh.new();bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(mesh);bm.free();mesh.update()
    obj=bpy.data.objects.new(name,mesh);sofa.objects.link(obj);obj.parent=root;obj.location=loc
    obj.rotation_euler.x=math.radians(rotation);obj.data.materials.append(fabric)
    for p in mesh.polygons:p.use_smooth=True
    uv_map(obj)
    return obj

def seam(obj,dims,r,face_axis):
    half=[d/2 for d in dims];axes=[i for i in range(3) if i!=face_axis]
    w,h=[half[i]-.014 for i in axes];rad=max(.01,r-.018)
    pts=[]
    for cx,cy,angle in [(w-rad,h-rad,0),(-w+rad,h-rad,90),(-w+rad,-h+rad,180),(w-rad,-h+rad,270)]:
        for i in range(10):
            theta=math.radians(angle+i*90/9)
            p=[0.,0.,0.];p[axes[0]]=cx+rad*math.cos(theta);p[axes[1]]=cy+rad*math.sin(theta)
            sign=-1 if face_axis==1 else 1;p[face_axis]=sign*half[face_axis]
            point=pillow_surface(p,half,r,face_axis,sign,.014 if face_axis==2 else .021)
            point[face_axis]+=sign*.0006;pts.append(point)
    curve=bpy.data.curves.new(obj.name+'_Seam','CURVE');curve.dimensions='3D';curve.bevel_depth=.0011;curve.bevel_resolution=2
    spline=curve.splines.new('POLY');spline.points.add(len(pts)-1)
    for p,v in zip(spline.points,pts):p.co=(*v,1)
    spline.use_cyclic_u=True
    s=bpy.data.objects.new(obj.name+'_Piping',curve);sofa.objects.link(s);s.parent=obj;s.data.materials.append(thread)

rounded('Base Upholstered Rail',(1.90,.89,.165),(0,-.012,.2725),.025,fabric)
rounded('Left Arm',(.165,.96,.52),(-1.0175,0,.45),.025,fabric)
rounded('Right Arm',(.165,.96,.52),(1.0175,0,.45),.025,fabric)
rounded('Rear Upholstered Panel',(1.88,.16,.61),(0,.397,.495),.035,fabric)
for sign,label in [(-1,'Left'),(1,'Right')]:
    seat=pillow(label+' Seat Cushion',(.927,.715,.165),(sign*.4735,-.094,.438),.045,bulge=.014)
    seam(seat,(.927,.715,.165),.045,2)
    back=pillow(label+' Back Cushion',(.929,.19,.475),(sign*.4745,.275,.706),.065,rotation=-12,bulge=.021)
    seam(back,(.929,.19,.475),.065,1)
for x,label in [(-1.018,'Left'),(1.018,'Right')]:
    for y,end in [(-.379,'Front'),(.365,'Rear')]:
        rounded(label+' '+end+' Steel Leg',(.048,.048,.205),(x,y,.1025),.003,steel,segments=3)

rounded('Studio Floor',(200,200,.08),(0,0,-.04),.001,floor_mat,segments=1,collection=studio)
world=bpy.data.worlds.new('FORMA Soft Ambient');scene.world=world
background=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
background.inputs['Color'].default_value=(.65,.65,.65,1);background.inputs['Strength'].default_value=.35
def aim(obj,point):obj.rotation_euler=(Vector(point)-obj.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,scale in [('Key Softbox',(-3,-4,4),450,4),('Fill Softbox',(3,-1,3),200,3),('Rim Softbox',(0,3,3),300,3)]:
    light=bpy.data.lights.new(name,'AREA');light.energy=power;light.shape=next(i.identifier for i in light.bl_rna.properties['shape'].enum_items if i.identifier.lower()=='disk');light.size=scale
    ob=bpy.data.objects.new(name,light);studio.objects.link(ob);ob.location=loc;aim(ob,(0,0,.45))
camera=bpy.data.cameras.new('FORMA Product Camera');ob=bpy.data.objects.new('FORMA Product Camera',camera);studio.objects.link(ob)
ob.location=(3.3,-5.5,2.6);aim(ob,(0,0,.48));camera.lens=58;scene.camera=ob
scene.render.resolution_x=1500;scene.render.resolution_y=1050;scene.render.resolution_percentage=100
scene.render.image_settings.file_format=next(i.identifier for i in scene.render.image_settings.bl_rna.properties['file_format'].enum_items if i.identifier.lower()=='png')
scene.render.filepath=os.path.join(OUT,'sofa-preview.png')
transforms=[i.identifier for i in scene.view_settings.bl_rna.properties['view_transform'].enum_items]
if 'AgX' in transforms:scene.view_settings.view_transform='AgX'
for obj in bpy.context.selected_objects:obj.select_set(False)
root.select_set(True);bpy.context.view_layer.objects.active=root
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.overlay.show_overlays=False
        area.spaces.active.shading.type='MATERIAL'
        area.spaces.active.region_3d.view_location=(0,0,.5)
        area.spaces.active.region_3d.view_distance=3.5
        area.spaces.active.region_3d.view_rotation=ob.rotation_euler.to_quaternion()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'forma-sofa.blend'))
print('Created scene:',scene.name,'Sofa objects:',len(sofa.objects),'Saved editable blend.')
