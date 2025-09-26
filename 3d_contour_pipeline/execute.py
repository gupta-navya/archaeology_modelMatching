import os
import json
import numpy as np
import cv2
import open3d as o3d

from pipeline_debug import (
    save_snapshot_from_plane,
    compute_plane_frame,
    project_vertices_to_plane,
    contour_from_2d_points,
    draw_2d_contour_to_image,
)
from find_stable_plane import (
    get_best_supported_face,
    get_opposite_face,
    save_face_info_json,
)
from icp_sbs import get_best_contour

def process_all_finds(base_dir=None, start=20, end=34):
    base_dir = base_dir or os.path.dirname(__file__)
    finds_dir = os.path.join(base_dir, "finds") #ireplace with input folder containing 3d model
    out_root = os.path.join(base_dir, "3d_contours") #output folder to store contour screenshots
    os.makedirs(out_root, exist_ok=True)

    for i in range(start, end + 1): #go from 1 to n (individual find folders)
        find_folder = os.path.join(finds_dir, str(i))
        mesh_path = os.path.join(find_folder, "a_0_mesh.ply") #assuming mesh file is named a_0_mesh.ply
        if not os.path.exists(mesh_path):
            print(f"[{i}] mesh not found: {mesh_path} -- skipping")
            continue

        out_folder = os.path.join(out_root, str(i))
        os.makedirs(out_folder, exist_ok=True)

        # load mesh
        mesh = o3d.io.read_triangle_mesh(mesh_path)
        if not mesh.has_triangles():
            print(f"[{i}] mesh has no triangles -- skipping")
            continue
        mesh.compute_triangle_normals()

        # compute stable plane / opposite face
        primary_face = get_best_supported_face(mesh, distance_threshold=0.01)
        opposite_face = get_opposite_face(mesh, primary_face, distance_threshold=0.01)

        # save face info json (uses helper from find_stable_plane)
        face_json_name = os.path.join(out_folder, "face_info.json") 
        save_face_info_json(primary_face, opposite_face, os.path.basename(mesh_path), face_json_name)

        # Snapshot from plane (renders aligned mesh and saves image)
        snapshot_path = os.path.join(out_folder, "snapshot.jpg")
        try:
            res = save_snapshot_from_plane(mesh_path, primary_face, snapshot_path)
            # save_snapshot_from_plane may return (path, view_params) or just path
            if isinstance(res, tuple):
                snapshot_path, view_params = res
        except Exception as e:
            print(f"[{i}] failed to save snapshot: {e}")
            snapshot_path = None

        # Method A: project vertices to the plane and compute contour (pure 3D projection)
        origin, u, v = compute_plane_frame(primary_face)
        pts2d = project_vertices_to_plane(mesh, origin, u, v)
        hull = contour_from_2d_points(pts2d, method="convex")
        proj_contour_img = os.path.join(out_folder, "projected_contour.jpg")
        draw_2d_contour_to_image(hull, proj_contour_img, padding=20, thickness=6, color=(0, 255, 0))

        # Method B: extract contour from rendered snapshot and overlay on snapshot (visual)
        snapshot_with_contour = os.path.join(out_folder, "snapshot_with_contour.jpg")
        contour_points = None
        if snapshot_path and os.path.exists(snapshot_path):
            img = cv2.imread(snapshot_path)
            if img is not None:
                contour_pts = get_best_contour(img)
                if contour_pts is not None and len(contour_pts) > 0:
                    pts = np.round(contour_pts).astype(int)
                    cv2.polylines(img, [pts.reshape((-1, 1, 2))], isClosed=True, color=(0, 255, 0), thickness=6)
                    cv2.imwrite(snapshot_with_contour, img)
                    contour_points = contour_pts.tolist()
                else:
                    # save original snapshot as fallback
                    cv2.imwrite(snapshot_with_contour, img)
            else:
                print(f"[{i}] could not read snapshot image at {snapshot_path}")
        else:
            print(f"[{i}] snapshot not available, skipped snapshot-based contour")

        # Save contour info JSON (both projected hull and snapshot-extracted contour if present)
        contour_info = {
            "mesh": os.path.basename(mesh_path),
            "face_json": os.path.basename(face_json_name),
            "projected_contour_image": os.path.basename(proj_contour_img) if os.path.exists(proj_contour_img) else None,
            "projected_contour_points": hull.tolist() if hull is not None else None,
            "snapshot_image": os.path.basename(snapshot_path) if snapshot_path and os.path.exists(snapshot_path) else None,
            "snapshot_with_contour_image": os.path.basename(snapshot_with_contour) if os.path.exists(snapshot_with_contour) else None,
            "snapshot_extracted_contour_points": contour_points,
        }
        with open(os.path.join(out_folder, "contour_info.json"), "w") as jf:
            json.dump(contour_info, jf, indent=2)

        print(f"[{i}] done -> {out_folder}")

if __name__ == "__main__":
    process_all_finds()