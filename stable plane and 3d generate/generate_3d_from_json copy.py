import json
import numpy as np
import open3d as o3d
import os
import time

def create_large_plane(mesh, center, normal, offset=0.001, color=[0, 1, 0]):
    center = np.array(center)
    normal = np.array(normal)
    normal /= np.linalg.norm(normal)

    bbox = mesh.get_axis_aligned_bounding_box()
    extent = bbox.get_extent()
    size = max(extent) * 1.5

    if abs(normal[2]) < 0.9:
        v1 = np.array([normal[1], -normal[0], 0])
    else:
        v1 = np.array([0, normal[2], -normal[1]])
    v1 /= np.linalg.norm(v1)
    v2 = np.cross(normal, v1)
    v2 /= np.linalg.norm(v2)

    center_offset = center + offset * normal

    corners = []
    for i in [-1, 1]:
        for j in [-1, 1]:
            corner = center_offset + i * size * v1 + j * size * v2
            corners.append(corner)

    plane = o3d.geometry.TriangleMesh()
    plane.vertices = o3d.utility.Vector3dVector(corners)
    plane.triangles = o3d.utility.Vector3iVector([[0, 1, 2], [1, 3, 2]])
    plane.paint_uniform_color(color)
    plane.compute_triangle_normals()
    return plane

def visualize_planes_on_mesh(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)

    mesh = o3d.io.read_triangle_mesh(data["ply_file"])
    mesh.compute_vertex_normals()

    vis = o3d.visualization.Visualizer()
    vis.create_window()
    vis.add_geometry(mesh)

    face_colors = {
        "primary_face": [1, 1, 1],
        "opposite_face": [1, 1, 1]
    }

    for face_key in ["primary_face", "opposite_face"]:
        face = data.get(face_key)
        if face:
            center = face["center"]
            normal = face["normal"]
            color = face_colors[face_key]
            plane = create_large_plane(mesh, center, normal, offset=0.001, color=color)
            vis.add_geometry(plane)

    primary_center = np.array(data["primary_face"]["center"])
    primary_normal = np.array(data["primary_face"]["normal"])
    camera_position = primary_center + 1.0 * primary_normal

    ctr = vis.get_view_control()
    ctr.set_lookat(primary_center)
    ctr.set_front(primary_center - camera_position)
    ctr.set_up([0, 1, 0])
    ctr.set_zoom(0.7)

    vis.poll_events()
    vis.update_renderer()
    vis.run()
    vis.destroy_window()
'''
def save_snapshots_from_planes(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)

    mesh = o3d.io.read_triangle_mesh(data["ply_file"])
    mesh.compute_vertex_normals()

    output_dir = "model_pics"
    os.makedirs(output_dir, exist_ok=True)

    for i, face_key in enumerate(["primary_face", "opposite_face"], start=1):
        face = data.get(face_key)
        if face:
            center = np.array(face["center"])
            normal = np.array(face["normal"])
            normal /= np.linalg.norm(normal)
            camera_position = center + 1.5 * normal

            vis = o3d.visualization.Visualizer()
            vis.create_window(visible=False)
            vis.add_geometry(mesh)

            ctr = vis.get_view_control()
            ctr.set_lookat(center)
            ctr.set_front(center - camera_position)
            ctr.set_up([0, 1, 0])
            ctr.set_zoom(0.7)

            vis.poll_events()
            vis.update_renderer()
            time.sleep(0.3)
            vis.capture_screen_image(os.path.join(output_dir, f"{i}.jpg"))
            vis.destroy_window()

'''
if __name__ == "__main__":
    json_path = "model_face_info.json"
    #save_snapshots_from_planes(json_path)
    visualize_planes_on_mesh(json_path)
    
