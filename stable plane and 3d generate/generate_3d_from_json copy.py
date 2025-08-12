import json
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

def visualize_oriented_mesh(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)

    mesh = o3d.io.read_triangle_mesh(data["ply_file"])
    mesh.compute_vertex_normals()

    primary_face = data["primary_face"]
    transform = compute_alignment_transform(primary_face["normal"], primary_face["center"])
    mesh.transform(transform)

    o3d.visualization.draw_geometries([mesh])

if __name__ == "__main__":
    visualize_oriented_mesh("model_face_info.json")
