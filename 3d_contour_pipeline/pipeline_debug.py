import os
import time
import json
import numpy as np
import open3d as o3d
import cv2
import matplotlib.pyplot as plt
from icp_sbs import get_best_contour
from find_stable_plane import get_best_supported_face, get_opposite_face, save_face_info_json

def save_snapshot_from_plane(mesh_path, face, output_path):
    """Render mesh from a camera placed along face normal and save a snapshot to output_path.

    If the optional view_params dict is provided (keys: front, up, zoom), this function will
    keep the same camera orientation/zoom and only update the lookat to the provided face center.
    When view_params is None the function computes a camera for this mesh and returns the
    captured view parameters so they can be reused for subsequent meshes.
    """
    # allow caller to pass a view_params via kwargs by packing/unpacking in callers
    # (we can't change signature broadly for compatibility in this repo edit)
    # Check if a tuple (output_path, view_params) style call is expected by caller.
    mesh = o3d.io.read_triangle_mesh(mesh_path)
    mesh.compute_vertex_normals()

    # darken mesh for clear contour
    mesh.vertex_colors = o3d.utility.Vector3dVector(
        np.tile([0.05, 0.05, 0.05], (np.asarray(mesh.vertices).shape[0], 1))
    )

    center = np.array(face["center"])
    normal = np.array(face["normal"])
    norm_len = np.linalg.norm(normal)
    if norm_len < 1e-12:
        # fallback to Z axis if normal is invalid
        normal = np.array([0.0, 0.0, 1.0])
    else:
        normal = normal / norm_len

    # rotate mesh so that the face normal aligns with +Z (make face lie on XY plane)
    z_axis = np.array([0.0, 0.0, 1.0])
    v = np.cross(normal, z_axis)
    c = np.dot(normal, z_axis)
    if np.linalg.norm(v) < 1e-6:
        R_align = np.eye(3)
    else:
        vx = np.array([[0, -v[2], v[1]],
                       [v[2], 0, -v[0]],
                       [-v[1], v[0], 0]])
        R_align = np.eye(3) + vx + vx @ vx * ((1 - c) / (np.linalg.norm(v) ** 2))

    # rotate mesh in-place around the face center
    try:
        mesh.rotate(R_align, center=center)
    except Exception:
        # fallback: rotate about origin then translate
        mesh.translate(-center)
        mesh.rotate(R_align)
        mesh.translate(center)

    vis = o3d.visualization.Visualizer()
    vis.create_window(visible=False, width=1400, height=1400)
    vis.get_render_option().mesh_show_back_face = True
    vis.add_geometry(mesh)

    ctr = vis.get_view_control()

    # If caller previously captured params and stored them on the mesh object or elsewhere,
    # they'll pass them via an attribute on the face dict ("view_params"). This keeps the
    # change minimal: if face contains 'view_params' we'll reuse it, otherwise compute one.
    view_params = face.get("view_params") if isinstance(face, dict) else None

    if view_params is None:
        # compute camera from bbox and face normal (first-time setup)
        bbox = mesh.get_axis_aligned_bounding_box()
        extent = bbox.get_extent()
        # zoom out more so entire model fits comfortably
        distance = max(extent) * 4
        # after aligning, camera looks along -Z; place it above +Z
        camera_position = center + distance * z_axis

        # use the geometric center of the whole mesh for the camera lookat
        mesh_center = np.asarray(mesh.get_center())
        ctr.set_lookat(mesh_center)
        ctr.set_front(mesh_center - camera_position)
        ctr.set_up([0, 1, 0])
        # slightly smaller zoom to show more of the model
        ctr.set_zoom(1)
        vis.poll_events()
        vis.update_renderer()
        # capture pinhole camera parameters so we can reuse them for other meshes
        try:
            params = ctr.convert_to_pinhole_camera_parameters()
            view_params = params
        except Exception:
            # fallback: store nothing
            view_params = None
    else:
        # reuse full pinhole camera parameters when available
        try:
            ctr.convert_from_pinhole_camera_parameters(view_params)
            # update lookat to current center to keep camera focused on this face
            ctr.set_lookat(np.asarray(mesh.get_center()))
        except Exception:
            # fallback to setting lookat only
            ctr.set_lookat(np.asarray(mesh.get_center()))
        vis.poll_events()
        vis.update_renderer()

    time.sleep(0.2)
    vis.capture_screen_image(output_path)
    vis.destroy_window()

    # return output and view_params so caller can reuse for next meshes
    return output_path, view_params
    
def show_image_cv2(img_path, window_name):
    img = cv2.imread(img_path)
    cv2.imshow(window_name, img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def compute_plane_frame(face):
    """Return origin, u, v axes for the plane defined by face (center, normal).

    origin: 3-vector, u/v: orthonormal axes lying on plane.
    """
    origin = np.array(face["center"])
    n = np.array(face["normal"])
    nlen = np.linalg.norm(n)
    if nlen < 1e-12:
        n = np.array([0.0, 0.0, 1.0])
    else:
        n = n / nlen
    # pick an arbitrary vector not parallel to n
    ref = np.array([1.0, 0.0, 0.0])
    if abs(np.dot(ref, n)) > 0.9:
        ref = np.array([0.0, 1.0, 0.0])
    u = np.cross(ref, n)
    u_norm = np.linalg.norm(u)
    if u_norm < 1e-12:
        u = np.array([1.0, 0.0, 0.0])
    else:
        u = u / u_norm
    v = np.cross(n, u)
    v_norm = np.linalg.norm(v)
    if v_norm < 1e-12:
        v = np.array([0.0, 1.0, 0.0])
    else:
        v = v / v_norm
    return origin, u, v


def project_vertices_to_plane(mesh, origin, u, v):
    """Project mesh vertices to 2D coordinates in plane frame (u,v) with origin."""
    verts = np.asarray(mesh.vertices)
    rel = verts - origin.reshape((1, 3))
    x = rel.dot(u)
    y = rel.dot(v)
    pts2d = np.vstack([x, y]).T
    return pts2d


def contour_from_2d_points(pts2d, method="convex"):
    """Return ordered contour points from 2D points. Uses convex hull by default."""
    if pts2d is None or len(pts2d) == 0:
        return None
    if len(pts2d) < 3:
        # nothing to hull, return unique points
        uniq = np.unique(pts2d, axis=0)
        return uniq
    ptsf = pts2d.astype(np.float32)
    # OpenCV convex hull expects Nx2
    try:
        hull = cv2.convexHull(ptsf)
        hull = hull.reshape((-1, 2))
    except Exception:
        # fallback to an internal monotone chain convex hull implementation
        def monotone_chain(points):
            # points: Nx2 array
            P = np.array(sorted(map(tuple, points.tolist())))
            if len(P) <= 1:
                return P
            def cross(o, a, b):
                return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
            lower = []
            for p in P:
                while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
                    lower.pop()
                lower.append(tuple(p))
            upper = []
            for p in P[::-1]:
                while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
                    upper.pop()
                upper.append(tuple(p))
            hull = np.array(lower[:-1] + upper[:-1])
            return hull

        hull = monotone_chain(ptsf.tolist())
    return hull


def draw_2d_contour_to_image(contour_pts, out_path, padding=20, thickness=4, color=(0, 255, 0)):
    """Rasterize contour points to a JPG image and save.

    contour_pts: Nx2 array in plane coordinates.
    """
    if contour_pts is None or len(contour_pts) == 0:
        return None
    # compute bounds
    minxy = contour_pts.min(axis=0)
    maxxy = contour_pts.max(axis=0)
    range_xy = maxxy - minxy
    if np.all(range_xy < 1e-6):
        # degenerate - create small image
        W = H = 200
        scale = 1.0
    else:
        scale = max(range_xy)
        # choose image such that the longest side maps to 800 px (reasonable)
        target_long = 800
        scale_factor = target_long / (scale + 1e-12)
        W = int(max(200, np.ceil(range_xy[0] * scale_factor) + 2 * padding))
        H = int(max(200, np.ceil(range_xy[1] * scale_factor) + 2 * padding))

    # map points to pixel coords
    if np.all(range_xy < 1e-6):
        px = np.full((len(contour_pts),), W // 2, dtype=int)
        py = np.linspace(padding, H - padding, len(contour_pts)).astype(int)
    else:
        ref = minxy
        px = ((contour_pts[:, 0] - ref[0]) * scale_factor).astype(int) + padding
        py = ((contour_pts[:, 1] - ref[1]) * scale_factor).astype(int) + padding

    img = np.ones((H, W, 3), dtype=np.uint8) * 255

    pts = np.vstack([px, py]).T.reshape((-1, 1, 2)).astype(np.int32)
    if len(pts) == 1:
        cv2.circle(img, tuple(pts[0, 0].tolist()), radius=max(2, thickness), color=color, thickness=-1)
    elif len(pts) == 2:
        cv2.line(img, tuple(pts[0, 0].tolist()), tuple(pts[1, 0].tolist()), color=color, thickness=thickness)
    else:
        cv2.polylines(img, [pts], isClosed=True, color=color, thickness=thickness)

    cv2.imwrite(out_path, img)
    return out_path


def process_single_mesh(mesh_path, out_dir, view_params=None, use_projection=False):
    """Compute primary face, save JSON, then either:
    - use_projection=True: project mesh vertices to face plane, compute hull and rasterize contour (no screenshot),
    - use_projection=False: render snapshot and extract contour from image as before.
    """
    mesh = o3d.io.read_triangle_mesh(mesh_path)
    if not mesh.has_triangles():
        # nothing to do
        return None
    mesh.compute_triangle_normals()

    primary_face = get_best_supported_face(mesh, distance_threshold=0.01)
    opposite_face = get_opposite_face(mesh, primary_face, distance_threshold=0.01)

    base = os.path.splitext(os.path.basename(mesh_path))[0]
    # create a per-find subfolder (use parent folder name, e.g., '1')
    find_name = os.path.basename(os.path.dirname(mesh_path))
    mesh_folder = os.path.join(out_dir, find_name)
    os.makedirs(mesh_folder, exist_ok=True)
    json_path = os.path.join(mesh_folder, f"{base}_face_info.json")
    save_face_info_json(primary_face, opposite_face, os.path.basename(mesh_path), json_path)
    img_path = os.path.join(mesh_folder, f"{base}_snapshot.jpg")
    returned_view = None
    if use_projection:
        # project vertices onto face plane and rasterize contour
        origin, u, v = compute_plane_frame(primary_face)
        pts2d = project_vertices_to_plane(mesh, origin, u, v)
        hull = contour_from_2d_points(pts2d, method="convex")
        out_contour_path = os.path.join(mesh_folder, f"{base}_contour.jpg")
        draw_2d_contour_to_image(hull, out_contour_path, padding=20, thickness=6, color=(0, 255, 0))
        return out_contour_path, None
    else:
        # attach previously captured view params to primary_face so save_snapshot_from_plane
        # can detect and reuse them (minimal API change)
        if view_params is not None:
            primary_face["view_params"] = view_params
            res = save_snapshot_from_plane(mesh_path, primary_face, img_path)
            # res will be (output_path, view_params) when view_params was provided
            if isinstance(res, tuple):
                img_path, returned_view = res
            else:
                img_path = res
                returned_view = view_params
        else:
            res = save_snapshot_from_plane(mesh_path, primary_face, img_path)
            # when no view_params passed, function returns (path, view_params)
            if isinstance(res, tuple):
                img_path, returned_view = res
            else:
                img_path = res
                returned_view = None

        # read image, get contour, draw and save
        img = cv2.imread(img_path)
        if img is None:
            return None
        contour = get_best_contour(img)
        # draw contour: contour is Nx2 array
        if contour is not None and len(contour) > 0:
            pts = np.round(contour).astype(int)
            # thicker line for better visibility
            cv2.polylines(img, [pts.reshape((-1, 1, 2))], isClosed=True, color=(0, 255, 0), thickness=6)
        out_with_contour = os.path.join(mesh_folder, f"{base}_contour.jpg")
        cv2.imwrite(out_with_contour, img)
        # return saved path and updated view_params for reuse
        return out_with_contour, returned_view

def apply_2d_alignment_to_3d_mesh(mesh, face, angle_deg, mean_2d, scale_2d):
    # keep definition for compatibility (not used in simplified flow)
    center = np.array(face["center"])
    normal = np.array(face["normal"])
    normal /= np.linalg.norm(normal)

    z_axis = np.array([0, 0, 1])
    v = np.cross(normal, z_axis)
    c = np.dot(normal, z_axis)
    if np.linalg.norm(v) < 1e-6:
        R_align = np.eye(3)
    else:
        vx = np.array([[0, -v[2], v[1]],
                       [v[2], 0, -v[0]],
                       [-v[1], v[0], 0]])
        R_align = np.eye(3) + vx + vx @ vx * ((1 - c) / (np.linalg.norm(v) ** 2))

    mesh.rotate(R_align, center=center)
    theta = np.radians(angle_deg)
    Rz = np.array([[np.cos(theta), -np.sin(theta), 0],
                   [np.sin(theta),  np.cos(theta), 0],
                   [0, 0, 1]])
    mesh.rotate(Rz, center=center)
    return mesh

'''
def show_final_aligned_mesh(json_path, angle_deg, mean_2d, scale_2d):
    with open(json_path, "r") as f:
        data = json.load(f)
    mesh = o3d.io.read_triangle_mesh(data["ply_file"])
    mesh.compute_vertex_normals()
    mesh = apply_2d_alignment_to_3d_mesh(mesh, data["primary_face"], angle_deg, mean_2d, scale_2d)
    o3d.visualization.draw_geometries([mesh], window_name="Final Aligned 3D Model")
'''

def show_final_aligned_mesh(json_path, angle_deg, mean_2d, scale_2d):
    with open(json_path, "r") as f:
        data = json.load(f)
    mesh = o3d.io.read_triangle_mesh(data["ply_file"])
    mesh.compute_vertex_normals()
    mesh = apply_2d_alignment_to_3d_mesh(mesh, data["primary_face"], angle_deg, mean_2d, scale_2d)

    vis = o3d.visualization.Visualizer()
    vis.create_window(window_name="Final Aligned 3D Model")
    vis.add_geometry(mesh)

    ctr = vis.get_view_control()
    params = ctr.convert_to_pinhole_camera_parameters()
    ctr.convert_from_pinhole_camera_parameters(params)

    vis.run()
    vis.destroy_window()

if __name__ == "__main__":
    # iterate finds/1-10/a_0_mesh.ply
    base_dir = os.path.dirname(__file__)
    finds_dir = os.path.join(base_dir, "finds")
    out_dir = os.path.join(base_dir, "3d_contours")
    os.makedirs(out_dir, exist_ok=True)

    for i in range(1,11): # process finds 1 to 10
        mesh_dir = os.path.join(finds_dir, str(i))
        mesh_path = os.path.join(mesh_dir, "a_0_mesh.ply")
        if not os.path.exists(mesh_path):
            print(f"mesh not found: {mesh_path}")
            continue
        # pass view_params to keep camera consistent after first capture and use snapshot flow
        if i == 1:
            result = process_single_mesh(mesh_path, out_dir, view_params=None, use_projection=False)
        else:
            # reuse view_params from previous successful run if available
            try:
                result = process_single_mesh(mesh_path, out_dir, view_params=shared_view_params, use_projection=False)
            except NameError:
                result = process_single_mesh(mesh_path, out_dir, view_params=None, use_projection=False)

        if result is None:
            print(f"Processing failed for {mesh_path}")
            continue

        out, returned_view = result
        # store shared view params for subsequent iterations
        if returned_view is not None:
            shared_view_params = returned_view

        print(f"Processed {mesh_path} -> {out}")
