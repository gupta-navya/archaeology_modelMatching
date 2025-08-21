import os
import time
import json
import numpy as np
import open3d as o3d
import cv2
import matplotlib.pyplot as plt
from icp_sbs import get_best_contour, normalize_scale, pca_angle, rotate, align_with_reflection_check_all, plot_contours

def save_snapshots_from_planes(json_path, output_dir="model_pics"):
    with open(json_path, "r") as f:
        data = json.load(f)

    mesh = o3d.io.read_triangle_mesh(data["ply_file"])
    mesh.compute_vertex_normals()

    os.makedirs(output_dir, exist_ok=True)
    img_paths = [] 

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
            img_path = os.path.join(output_dir, f"{i}.jpg")
            vis.capture_screen_image(img_path)
            vis.destroy_window()
            img_paths.append(img_path)
    return img_paths

def show_image_cv2(img_path, window_name):
    img = cv2.imread(img_path)
    cv2.imshow(window_name, img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def align_and_show(img1_path, img2_path):
    # Step 1: Extract contours
    contour_2d = get_best_contour(img1_path)
    contour_3d = get_best_contour(img2_path)

    # Step A: Raw contours
    #plot_contours(contour_2d, contour_3d, "Step A: Raw Contours")

    # Step B: Normalized contours
    norm_2d, mean_2d, scale_2d = normalize_scale(contour_2d)
    norm_3d, _, _ = normalize_scale(contour_3d)
    #plot_contours(norm_2d, norm_3d, "Step B: Normalized Contours")

    # Step C: PCA-aligned orientations
    angle_2d = pca_angle(norm_2d)
    angle_3d = pca_angle(norm_3d)
    rotated_3d = rotate(norm_3d, angle_2d - angle_3d)
    #plot_contours(norm_2d, rotated_3d, "Step C: PCA Orientation Aligned")

    # Step D: ICP with reflection check
    aligned_3d_norm = align_with_reflection_check_all(rotated_3d, norm_2d)
    #plot_contours(norm_2d, aligned_3d_norm, "Step D: ICP-Aligned (Normalized Space)")

    # Step E: Rescale to original space
    final_3d = aligned_3d_norm * scale_2d + mean_2d
    #plot_contours(contour_2d, final_3d, "Step E: Final Alignment (Original Space)")

    # Compute transformation (rotation + translation) in 2D
    # For 3D, you need to lift this to 3D (see below)
    return angle_2d - angle_3d, mean_2d, scale_2d

def apply_2d_alignment_to_3d_mesh(mesh, face, angle_deg, mean_2d, scale_2d):
    # This is a simplified version: assumes the primary face is parallel to XY
    # and the 2D image is a projection onto XY. For more general cases, use PnP or 3D-2D registration.
    center = np.array(face["center"])
    normal = np.array(face["normal"])
    normal /= np.linalg.norm(normal)

    # 1. Rotate mesh so that face normal aligns with +Z
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

    # 2. Rotate in-plane by angle_deg about Z
    theta = np.radians(angle_deg)
    Rz = np.array([[np.cos(theta), -np.sin(theta), 0],
                   [np.sin(theta),  np.cos(theta), 0],
                   [0, 0, 1]])
    mesh.rotate(Rz, center=center)

    # 3. (Optional) Translate mesh so that face center is at mean_2d (if you want to match 2D image position)
    # mesh.translate(mean_2d[:2] - center[:2])

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

    # Your before and after extrinsics (from your earlier message)
    E_before = np.array([
        [ 1.,  0.,  0., -6.52592526],
        [-0., -1., -0., -6.33827315],
        [-0., -0., -1., 35.26014936],
        [ 0.,  0.,  0.,  1.]
    ])
    E_after = np.array([
        [-0.99071542, -0.08131189,  0.10895568,  6.12155619],
        [ 0.07458569, -0.99512945, -0.0644543,  -6.89565441],
        [ 0.1136659,  -0.05572933,  0.99195479, 37.30235108],
        [ 0.,          0.,          0.,          1.        ]
    ])

    # Compute the transformation
    T = E_after @ np.linalg.inv(E_before)
    # Apply this transformation to the current extrinsic
    params.extrinsic = T @ params.extrinsic
    ctr.convert_from_pinhole_camera_parameters(params)

    vis.run()
    vis.destroy_window()

if __name__ == "__main__":
    # Step 1: Generate and show snapshots from both faces
    json_path = "model_face_info.json"
    img_find_path = "img.jpg"  # 2D find photograph

    #print("Generating 3D model snapshots...")
    img_paths = save_snapshots_from_planes(json_path)
    img1_path, img2_path = img_paths[0], img_paths[1]

    #print("Showing 3D model snapshot (primary face)...")
    #show_image_cv2(img1_path, "Primary Face Snapshot (1.jpg)")
    #print("Showing 3D model snapshot (opposite face)...")
    #show_image_cv2(img2_path, "Opposite Face Snapshot (2.jpg)")
    #print("Showing 2D find photograph...")
    #show_image_cv2(img_find_path, "Find Photograph (img.jpg)")

    # Step 2: Align contours and show each step
    #print("Running contour alignment and ICP...")
    angle_deg, mean_2d, scale_2d = align_and_show(img_find_path, img1_path)

    # Step 3: Show final aligned 3D model
    #print("Showing final aligned 3D model...")
    show_final_aligned_mesh(json_path, angle_deg, mean_2d, scale_2d)