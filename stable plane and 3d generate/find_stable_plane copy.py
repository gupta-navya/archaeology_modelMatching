import numpy as np
import open3d as o3d
import trimesh
import os
import json

def trimesh_to_open3d(tri_mesh):
    mesh_o3d = o3d.geometry.TriangleMesh()
    mesh_o3d.vertices = o3d.utility.Vector3dVector(tri_mesh.vertices)
    mesh_o3d.triangles = o3d.utility.Vector3iVector(tri_mesh.faces)
    mesh_o3d.compute_vertex_normals()
    mesh_o3d.compute_triangle_normals()
    return mesh_o3d

def get_opposite_faces(mesh, distance_threshold=0.01, angle_threshold=15):
    vertices = np.asarray(mesh.vertices)
    triangles = np.asarray(mesh.triangles)
    triangle_normals = np.asarray(mesh.triangle_normals)

    face_supports = []
    for i, tri in enumerate(triangles):
        v0, v1, v2 = [vertices[j] for j in tri]
        normal = triangle_normals[i]
        normal /= np.linalg.norm(normal)
        d = -np.dot(normal, v0)

        distances = np.abs(vertices @ normal + d)
        support_indices = np.where(distances < distance_threshold)[0]
        support_count = len(support_indices)

        face_supports.append({
            "index": i,
            "support_count": support_count,
            "normal": normal.tolist(),
            "center": np.mean([v0, v1, v2], axis=0).tolist(),
            "supporting_vertices": support_indices.tolist()
        })

    face_supports.sort(key=lambda x: x["support_count"], reverse=True)

    if not face_supports:
        return [], []

    primary_face = face_supports[0]
    opposite_face = None

    for face in face_supports[1:]:
        angle = np.degrees(np.arccos(np.clip(np.dot(primary_face["normal"], face["normal"]), -1, 1)))
        if angle > (180 - angle_threshold):
            opposite_face = face
            break

    if opposite_face is None and len(face_supports) > 1:
        opposite_face = face_supports[1]

    return primary_face, opposite_face

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

def load_or_reconstruct_mesh(ply_path):
    mesh = trimesh.load(ply_path)
    if isinstance(mesh, trimesh.Scene):
        meshes = [g for g in mesh.geometry.values() if isinstance(g, trimesh.Trimesh)]
        if not meshes:
            raise TypeError("Scene contains no valid Trimesh geometries.")
        mesh = trimesh.util.concatenate(meshes)
    elif isinstance(mesh, trimesh.Trimesh):
        return mesh
    else:
        pcd = o3d.io.read_point_cloud(ply_path)
        if len(pcd.points) == 0:
            raise TypeError("File is neither a mesh nor a valid point cloud.")
        pcd.estimate_normals()
        mesh_o3d, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=8)
        mesh_o3d = mesh_o3d.crop(pcd.get_axis_aligned_bounding_box())
        vertices = np.asarray(mesh_o3d.vertices)
        faces = np.asarray(mesh_o3d.triangles)
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
    return mesh

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

def save_face_info_json(primary_face, opposite_face, ply_filename, output_path):
    data = {
        "ply_file": ply_filename,
        "primary_face": primary_face,
        "opposite_face": opposite_face
    }
    with open(output_path, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Saved face info to {output_path}")

if __name__ == "__main__":
    input_path = "model.ply"
    base_name = os.path.splitext(os.path.basename(input_path))[0]

    mesh = load_or_reconstruct_mesh(input_path)
    hull = mesh.convex_hull
    hull_o3d = trimesh_to_open3d(hull)

    primary_face, opposite_face = get_opposite_faces(hull_o3d, distance_threshold=0.01)

    output_dir = f"{base_name}_pics"
    os.makedirs(output_dir, exist_ok=True)

    colored_mesh = o3d.io.read_triangle_mesh(input_path)
    colored_mesh.compute_vertex_normals()

    for i, face in enumerate([primary_face, opposite_face]):
        if face:
            transform = compute_alignment_transform(face["normal"], face["center"])
            output_path = os.path.join(output_dir, f"{base_name}_view_{i+1}.png")
            save_snapshot(colored_mesh, transform, output_path)

    json_path = os.path.join(os.path.dirname(input_path), f"{base_name}_face_info.json")
    save_face_info_json(primary_face, opposite_face, os.path.basename(input_path), json_path)
