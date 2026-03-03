import bpy
import os
import sys
import mathutils

# Clear the scene - remove default objects
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    # Also clear mesh data blocks
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)

# Setup camera to frame the object
def setup_camera(obj):
    # Add camera
    bpy.ops.object.camera_add(location=(3, -3, 2))
    camera = bpy.context.object
    camera.rotation_euler = (64 * 3.14159/180, 0, 45 * 3.14159/180)  # Convert to radians
    
    # Set as active camera
    bpy.context.scene.camera = camera
    
    # Optional: Add track to constraint to keep camera pointed at object
    track = camera.constraints.new(type='TRACK_TO')
    track.target = obj
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'
    
    return camera

# Setup lighting
def setup_lights():
    # Key light (main light)
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun = bpy.context.object
    sun.data.energy = 3
    sun.rotation_euler = (45 * 3.14159/180, 0, 45 * 3.14159/180)
    
    # Fill light (to soften shadows)
    bpy.ops.object.light_add(type='POINT', location=(-3, -3, 3))
    fill = bpy.context.object
    fill.data.energy = 100
    fill.data.color = (0.8, 0.9, 1.0)  # Slightly blue for ambiance
    
    # Back light (rim light)
    bpy.ops.object.light_add(type='POINT', location=(0, 3, 2))
    back = bpy.context.object
    back.data.energy = 150
    back.data.color = (1.0, 0.9, 0.8)  # Slightly warm

# Import PLY file
def import_ply(filepath):
    # Check if file exists
    if not os.path.exists(filepath):
        print(f"Error: File {filepath} not found!")
        return None
    
    # Import PLY
    bpy.ops.wm.ply_import(filepath=filepath)
    
    # Get the imported object (it should be the active object)
    imported = bpy.context.active_object
    if imported is None:
        print("Error: No object imported!")
        return None
    
    print(f"Successfully imported {filepath}")
    return imported

# Configure material
def add_material(obj, color=(0.3, 0.5, 0.8, 1.0)):
    # Create new material
    mat = bpy.data.materials.new(name="MeshMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create Principled BSDF
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.inputs['Base Color'].default_value = color
    principled.inputs['Roughness'].default_value = 0.3
    principled.inputs['Metallic'].default_value = 0.0
    
    # Create output node
    output = nodes.new(type='ShaderNodeOutputMaterial')
    
    # Link them
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    # Assign material to object
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    
    return mat

# Main rendering function
def render_ply(ply_path, output_path="render_output.png", resolution=(1920, 1080)):
    print("Starting render process...")
    
    # Clear scene
    clear_scene()
    print("Scene cleared")
    
    # Import mesh
    mesh_obj = import_ply(ply_path)
    if mesh_obj is None:
        return False
    
    # Center and scale the object
    mesh_obj.location = (0, 0, 0)
    
    # Add material (customize color here)
    add_material(mesh_obj, color=(0.8, 0.3, 0.2, 1.0))  # Reddish color
    
    # Setup lights
    setup_lights()
    print("Lights added")
    
    # Setup camera
    camera = setup_camera(mesh_obj)
    print("Camera positioned")
    
    # Configure render settings
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'  # Use Cycles for better quality
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.filepath = output_path
    
    # Optional: Transparent background
    scene.render.film_transparent = True
    
    # Cycles settings
    scene.cycles.samples = 128  # Higher = better quality, slower render
    scene.cycles.use_denoising = True  # Reduce noise
    
    # Use GPU if available
    cycles_prefs = bpy.context.preferences.addons['cycles'].preferences
    cycles_prefs.compute_device_type = 'CUDA'  # or 'OPENCL' or 'OPTIX'
    cycles_prefs.get_devices()
    for device in cycles_prefs.devices:
        device.use = True  # Enable all devices
    
    # Render
    print(f"Rendering to {output_path}...")
    bpy.ops.render.render(write_still=True)
    print(f"Render complete! Saved to {output_path}")
    
    return True

if __name__ == "__main__":
    # Configure paths
    ply_file = "./meshes/1.ply"  # Adjust path as needed
    output_file = "./my_render.png"
    
    # Run render
    success = render_ply(ply_file, output_file, resolution=(1280, 720))
    
    if success:
        print("✅ Render successful!")
    else:
        print("❌ Render failed")
