import numpy as np
import open3d as o3d
import trimesh

def trimesh_to_open3d(tri_mesh):
    mesh_o3d = o3d.geometry.TriangleMesh()
    mesh_o3d.vertices = o3d.utility.Vector3dVector(tri_mesh.vertices)
    mesh_o3d.triangles = o3d.utility.Vector3iVector(tri_mesh.faces)
    mesh_o3d.compute_vertex_normals()
    mesh_o3d.compute_triangle_normals()
    return mesh_o3d

def get_best_supported_face(mesh, distance_threshold=0.01):
    vertices = np.asarray(mesh.vertices)
    triangles = np.asarray(mesh.triangles)
    max_support = -1
    best_index = 0

    for i, tri in enumerate(triangles):
        v0, v1, v2 = [vertices[j] for j in tri]
        normal = np.cross(v1 - v0, v2 - v0)
        normal /= np.linalg.norm(normal)
        d = -np.dot(normal, v0)

        distances = np.abs(vertices @ normal + d)
        support = np.count_nonzero(distances < distance_threshold)

        if support > max_support:
            max_support = support
            best_index = i

    return best_index

def create_plane_on_face(mesh, face_index, offset=0.05):
    triangle = mesh.triangles[face_index]
    vertices = np.asarray(mesh.vertices)[triangle]

    face_normal = mesh.triangle_normals[face_index]
    face_normal /= np.linalg.norm(face_normal)

    bbox = mesh.get_axis_aligned_bounding_box()
    extent = bbox.get_extent()
    size = max(extent) * 1.5

    # Create orthogonal vectors to face normal
    if abs(face_normal[2]) < 0.9:
        v1 = np.array([face_normal[1], -face_normal[0], 0])
    else:
        v1 = np.array([0, face_normal[2], -face_normal[1]])
    v1 /= np.linalg.norm(v1)
    v2 = np.cross(face_normal, v1)
    v2 /= np.linalg.norm(v2)

    face_center = np.mean(vertices, axis=0)
    plane_center = face_center + offset * face_normal  # Push plane away from face

    corners = []
    for i in [-1, 1]:
        for j in [-1, 1]:
            corner = plane_center + i * size * v1 + j * size * v2
            corners.append(corner)

    plane = o3d.geometry.TriangleMesh()
    plane.vertices = o3d.utility.Vector3dVector(corners)
    plane.triangles = o3d.utility.Vector3iVector([[0, 1, 2], [1, 3, 2]])
    plane.paint_uniform_color([0, 1, 0])  # Green
    plane.compute_triangle_normals()
    return plane

def snap_flat_face(mesh, flat_face_index, offset_distance=1.0):
    triangle = mesh.triangles[flat_face_index]
    vertices = np.asarray(mesh.vertices)[triangle]
    face_center = np.mean(vertices, axis=0)

    model_center = np.mean(np.asarray(mesh.vertices), axis=0)
    face_normal = mesh.triangle_normals[flat_face_index]

    if np.dot(face_normal, model_center - face_center) > 0:
        face_normal = -face_normal

    camera_position = face_center + face_normal * offset_distance

    vis = o3d.visualization.Visualizer()
    vis.create_window(window_name="Convex Hull with Floating Plane", width=800, height=800)
    vis.add_geometry(mesh)

    green_plane = create_plane_on_face(mesh, flat_face_index, offset=0.5)  # Increased offset
    vis.add_geometry(green_plane)

    ctr = vis.get_view_control()
    ctr.set_lookat(face_center)
    ctr.set_front(face_center - camera_position)
    ctr.set_up([0, 1, 0])
    ctr.set_zoom(0.7)

    render_opt = vis.get_render_option()
    render_opt.background_color = np.array([1.0, 1.0, 1.0])
    render_opt.mesh_show_wireframe = True
    render_opt.mesh_show_back_face = True
    render_opt.line_width = 1.5

    vis.poll_events()
    vis.update_renderer()
    vis.run()
    vis.destroy_window()

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

# Main entry point
if __name__ == "__main__":
    mesh = load_or_reconstruct_mesh("model.ply")
    hull = mesh.convex_hull
    hull_o3d = trimesh_to_open3d(hull)
    flat_face_index = get_best_supported_face(hull_o3d, distance_threshold=0.01)
    snap_flat_face(hull_o3d, flat_face_index, offset_distance=1.5)
