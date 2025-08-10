import json
import os
import numpy as np
import open3d as o3d

def compute_alignment_transform(normal, center):
    normal = np.array(normal)
    center = np.array(center)
    normal /= np.linalg.norm(normal)

    target_normal = np.array([0, 0, 1])
    v = np.cross(normal, target_normal)
    c = np.dot(normal, target_normal)
    s = np.linalg.norm(v)

    if s == 0:
        R = np.eye(3)
    else:
        vx = np.array([[0, -v[2], v[1]],
                       [v[2], 0, -v[0]],
                       [-v[1], v[0], 0]])
        R = np.eye(3) + vx + vx @ vx * ((1 - c) / (s ** 2))

    T = -R @ center

    transform = np.eye(4)
    transform[:3, :3] = R
    transform[:3, 3] = T

    return transform

def save_snapshot(mesh, transform, filename):
    vis = o3d.visualization.Visualizer()
    vis.create_window(width=800, height=600, visible=False)

    transformed_mesh = o3d.geometry.TriangleMesh(mesh)
    transformed_mesh.transform(transform)

    vis.add_geometry(transformed_mesh)

    ctr = vis.get_view_control()
    ctr.set_front([0, 0, -1])
    ctr.set_up([0, 1, 0])
    ctr.set_zoom(0.8)

    vis.poll_events()
    vis.update_renderer()
    vis.capture_screen_image(filename)
    vis.destroy_window()
    print(f"Saved snapshot to {filename}")

if __name__ == "__main__":
    json_path = "model_face_info.json"

    with open(json_path, "r") as f:
        data = json.load(f)

    ply_file = data["ply_file"]
    base_name = os.path.splitext(os.path.basename(ply_file))[0]
    output_dir = "json_pics"
    os.makedirs(output_dir, exist_ok=True)

    mesh = o3d.io.read_triangle_mesh(ply_file)
    mesh.compute_vertex_normals()

    for i, face_key in enumerate(["primary_face", "opposite_face"]):
        face = data.get(face_key)
        if face:
            transform = compute_alignment_transform(face["normal"], face["center"])
            output_path = os.path.join(output_dir, f"{base_name}_json_view_{i+1}.png")
            save_snapshot(mesh, transform, output_path)
