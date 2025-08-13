import numpy as np
import open3d as o3d
import os
import json

def reconstruct_mesh_from_pointcloud(pcd_path, depth=8):
    pcd = o3d.io.read_point_cloud(pcd_path)
    pcd.estimate_normals()
    mesh, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=depth)
    mesh = mesh.crop(pcd.get_axis_aligned_bounding_box())
    mesh.compute_triangle_normals()
    return mesh

def get_best_supported_face(mesh, distance_threshold=0.01):
    vertices = np.asarray(mesh.vertices)
    triangles = np.asarray(mesh.triangles)
    triangle_normals = np.asarray(mesh.triangle_normals)

    max_support = -1
    best_index = None

    for i, tri in enumerate(triangles):
        v0, v1, v2 = [vertices[j] for j in tri]
        normal = triangle_normals[i]
        normal /= np.linalg.norm(normal)
        d = -np.dot(normal, v0)

        distances = np.abs(vertices @ normal + d)
        support_indices = np.where(distances < distance_threshold)[0]
        support_count = len(support_indices)

        if support_count > max_support:
            max_support = support_count
            best_index = i
            best_normal = normal
            best_center = np.mean([v0, v1, v2], axis=0)
            best_supporting_vertices = support_indices.tolist()

    return {
        "index": best_index,
        "support_count": max_support,
        "normal": best_normal.tolist(),
        "center": best_center.tolist(),
        "supporting_vertices": best_supporting_vertices
    }

def get_opposite_face(mesh, primary_face, distance_threshold=0.01, angle_threshold=150):
    vertices = np.asarray(mesh.vertices)
    triangles = np.asarray(mesh.triangles)
    triangle_normals = np.asarray(mesh.triangle_normals)

    primary_normal = np.array(primary_face["normal"])
    primary_center = np.array(primary_face["center"])

    best_score = -1
    best_face = None

    for i, tri in enumerate(triangles):
        if i == primary_face["index"]:
            continue

        v0, v1, v2 = [vertices[j] for j in tri]
        normal = triangle_normals[i]
        normal /= np.linalg.norm(normal)
        dot = np.dot(primary_normal, normal)
        angle = np.degrees(np.arccos(np.clip(dot, -1, 1)))

        if angle < angle_threshold:
            continue

        d = -np.dot(normal, v0)
        distances = np.abs(vertices @ normal + d)
        support_indices = np.where(distances < distance_threshold)[0]
        support_count = len(support_indices)

        center = np.mean([v0, v1, v2], axis=0)
        separation = np.linalg.norm(center - primary_center)

        score = support_count * separation  # prioritize distant + supported

        if score > best_score:
            best_score = score
            best_face = {
                "index": i,
                "support_count": support_count,
                "normal": normal.tolist(),
                "center": center.tolist(),
                "supporting_vertices": support_indices.tolist()
            }

    return best_face

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
    json_path = os.path.join(os.path.dirname(input_path), f"{base_name}_face_info.json")

    # Load mesh
    mesh = o3d.io.read_triangle_mesh(input_path)
    if not mesh.has_triangles():
        mesh = reconstruct_mesh_from_pointcloud(input_path)
    mesh.compute_triangle_normals()

    # Find primary and opposite faces
    primary_face = get_best_supported_face(mesh, distance_threshold=0.01)
    opposite_face = get_opposite_face(mesh, primary_face, distance_threshold=0.01)

    # Save JSON
    save_face_info_json(primary_face, opposite_face, os.path.basename(input_path), json_path)
