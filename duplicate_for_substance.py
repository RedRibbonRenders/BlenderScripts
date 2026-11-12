# AI Usage: No Direct Usage.
# Warning: Modifies and Manipulates Scene. USE AT YOUR OWN RISK. Make a backup first.

# Tool takes a single armature with potentially several meshes and replicates that armature several times. For each time, unique shapekeys and bone poses can be set.
# Recommend the active Blender file backed up before using.
# Update object_name, space_between_each and alts[]. Samples are provided below.
# After the script is run, the user will need to apply the shape keys on the new meshes and apply the armature's pose to the meshes.

from dataclasses import dataclass

import bpy
import mathutils

ZERO_3 = (0, 0, 0)
ZERO_4 = (0, 0, 0, 0)
ONE_3 = (1, 1, 1)

@dataclass
class BoneChange:
    location: (float, float, float) = ZERO_3
    rotation: (float, float, float, float) = ZERO_4
    scale: (float, float, float) = ONE_3

@dataclass
class MeshChange:
    shape_keys: dict[str, float]

@dataclass
class Alt:
    mesh: dict[str, MeshChange]
    armature: dict[str, BoneChange]


# --- details ---
# The object that will be replicated
object_name = "Armature"
# How far away from the original object each future one will be moved.
space_between_each = (0, 0, 10)

# Unique configuration per additional copy. Can set shape keys and pose bones.
# Each Alt contains 2 dictionaries.
# In the first dictionary, we store a collection of meshes and shapekeyes. For each listed mesh, it will iterate through the list of mesh changes and update the specific shapekeys to their provided values.
# In the second dictionary, we store a collection of bones and how those bones should be posed, affecting location, rotation and scale.
alts = [
    Alt(
        {'Cube': MeshChange({'A': 1})},
        {
            'Bone.004': BoneChange(rotation = (0.842, -0.495, -0.163, 1)),
            'Bone.002': BoneChange(rotation = (0.982, 0.038, 0.133, -0.132), scale = (2.682, 2.682, 2.682)),
        }),
    Alt(
        {'Cube': MeshChange({'B': 1})},
        {}
    ),
    Alt(
        {'Cube': MeshChange({'A': 1, 'B': 1})},
        {'Bone.003': BoneChange(scale = (0.403, 0.403, 0.403))}
    )   
]
# ---------------

def duplicate_name(name, i):
    return f'{name}.{i:03}'


def get_children(obj):
    yield obj
    for child in obj.children:
        for c in get_children(child):
            yield c

def deselect_all():
    print('deselecting all')
    bpy.ops.object.select_all(action='DESELECT')        
        

def select_only(*objs):
    deselect_all()
    for o in objs:
        print(f'Selecting {o}')
        o.select_set(True)


def find_child(parent, child_name):
    for c in parent.children:
        if c.name == child_name or c.name.startswith(f'{child_name}.'):
            print(f'found: {c}')
            return c


def find_child_as(parent, child_name, type):
    val = find_child(parent, child_name)
    if not (val.type == type):
        print(f'wrong type for {parent}/{child_name}. Expected {type} got {val.type}')
        return None
    return val.data


def get_shape_keys_for(mesh):
    for keys in bpy.data.shape_keys:
        if keys.user == mesh:
            return keys


def pose_bones(armature, changes):
    pose = bpy.data.objects[armature.name].pose
    for k, v in changes.items():
        cur_bone = pose.bones.get(k)
        cur_bone.location = v.location
        cur_bone.rotation_quaternion = v.rotation
        cur_bone.scale = v.scale


def update_shape_keys(mesh, changes):
    all_keys = get_shape_keys_for(mesh)
    
    if not all_keys:
        print(f'could not find shape_keys for ${mesh}')
        return
    
    all_key_blocks = all_keys.key_blocks
        
    for key, value in changes.shape_keys.items():
        all_key_blocks[key].value = value
    

def create_duplicate_and_update(parent, cur_index, move_offset, alt):
    
    objs = [i for i in get_children(parent)]
    select_only(*objs)

    bpy.ops.object.duplicate()
    
    new_name = duplicate_name(parent.name, cur_index)
    print(new_name)
    
    new_obj = bpy.data.objects.get(new_name)
    select_only(new_obj)
    
    x, y, z = move_offset
    bpy.ops.transform.translate(value=(x * cur_index, y * cur_index, z * cur_index))
    
    for mesh_name, change in alt.mesh.items():
        mesh = find_child_as(new_obj, mesh_name, 'MESH')
        if not mesh:
            print(f'could not find mesh {mesh_name} in {new_obj}')
            continue
        update_shape_keys(mesh, change)
        
        armature = bpy.data.armatures[new_name]
        if not armature:
            print(f'{new_name} is not an armature')
            continue
    
    pose_bones(armature, alt.armature)



def find_duplicate_and_update(name, alts, offset):
    root = bpy.data.objects.get(name)
    
    for idx, alt in enumerate(alts):
        create_duplicate_and_update(root, idx + 1, offset, alt)


find_duplicate_and_update(object_name, alts, space_between_each)
