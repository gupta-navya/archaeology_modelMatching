import os
import time
import json
import numpy as np
import open3d as o3d
import cv2
import matplotlib.pyplot as plt
from icp_sbs import get_best_contour, normalize_scale, pca_angle, rotate, align_with_reflection_check_all,plot_contours

def save_snapshots_from_planes(json_path, output_dir="model_pics"):
    with open(json_path, "r") as f:
        data = json.load(f)

    mesh_path = data["ply_file"]
    os.makedirs(output_dir, exist_ok=True)
    img_paths = []

    face = data.get("primary_face")
    mesh = o3d.io.read_triangle_mesh(mesh_path)  # Reload mesh each time
    mesh.compute_vertex_normals()
    center = np.array(face["center"])
    normal = np.array(face["normal"])
    normal /= np.linalg.norm(normal)
    bbox = mesh.get_axis_aligned_bounding_box()
    extent = bbox.get_extent()
    distance = max(extent) * 1.5
    camera_position = center + distance * normal

    vis = o3d.visualization.Visualizer()
    vis.create_window(visible=False)
    vis.get_render_option().mesh_show_back_face = True
    vis.add_geometry(mesh)

    ctr = vis.get_view_control()
    ctr.set_lookat(center)
    ctr.set_front(center - camera_position)
    ctr.set_up([0, 1, 0])
    ctr.set_zoom(0.7)
    vis.poll_events()
    vis.update_renderer()
    time.sleep(0.3)
    img_path = os.path.join(output_dir, "1.jpg")
    vis.capture_screen_image(img_path)
    #vis.destroy_window()
    img_paths.append(img_path)

    face= data.get("opposite_face")
    mesh = o3d.io.read_triangle_mesh(mesh_path)  # Reload mesh each time
    mesh.compute_vertex_normals()
    center = np.array(face["center"])
    normal = np.array(face["normal"])
    normal /= np.linalg.norm(normal)
    bbox = mesh.get_axis_aligned_bounding_box()
    extent = bbox.get_extent()
    distance = max(extent) * 1.5
    camera_position = center + distance * normal

    vis2 = o3d.visualization.Visualizer()
    vis2.create_window(visible=False)
    vis2.get_render_option().mesh_show_back_face = True
    vis2.add_geometry(mesh)

    ctr = vis2.get_view_control()
    ctr.set_lookat(center)
    ctr.set_front(center - camera_position)
    ctr.set_up([0, 1, 0])
    ctr.set_zoom(0.7)
    vis2.poll_events()
    vis2.update_renderer()
    time.sleep(0.3)
    img_path = os.path.join(output_dir, "2.jpg")
    vis2.capture_screen_image(img_path)
    #vis.destroy_window()
    img_paths.append(img_path)
    return img_paths
    
def show_image_cv2(img_path, window_name):
    img = cv2.imread(img_path)
    cv2.imshow(window_name, img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def align_and_show(img1, img2):
    contour_2d = get_best_contour(img1)
    contour_3d = get_best_contour(img2)
    '''plot_contours(contour_2d, contour_3d, "Step A: Raw Contours")

    # Step B: Normalized contours
    norm_2d, mean_2d, scale_2d = normalize_scale(contour_2d)
    norm_3d, _, _ = normalize_scale(contour_3d)
    plot_contours(norm_2d, norm_3d, "Step B: Normalized Contours")

    # Step C: PCA-aligned orientations
    angle_2d = pca_angle(norm_2d)
    angle_3d = pca_angle(norm_3d)
    rotated_3d = rotate(norm_3d, angle_2d - angle_3d)
    plot_contours(norm_2d, rotated_3d, "Step C: PCA Orientation Aligned")

    # Step D: ICP with reflection check
    aligned_3d_norm = align_with_reflection_check_all(rotated_3d, norm_2d)
    plot_contours(norm_2d, aligned_3d_norm, "Step D: ICP-Aligned (Normalized Space)")

    # Step E: Rescale to original space
    final_3d = aligned_3d_norm * scale_2d + mean_2d
    plot_contours(contour_2d, final_3d, "Step E: Final Alignment (Original Space)")'''
    
    norm_2d, mean_2d, scale_2d = normalize_scale(contour_2d)
    norm_3d, _, _ = normalize_scale(contour_3d)
    angle_2d = pca_angle(norm_2d)
    angle_3d = pca_angle(norm_3d)
    rotated_3d = rotate(norm_3d, angle_2d - angle_3d)
    aligned_3d_norm, error = align_with_reflection_check_all(rotated_3d, norm_2d)
    final_3d = aligned_3d_norm * scale_2d + mean_2d
    return angle_2d - angle_3d, mean_2d, scale_2d, error

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
    ctr.convert_from_pinhole_camera_parameters(params)

    vis.run()
    vis.destroy_window()

if __name__ == "__main__":
    json_path = "model_face_info.json"
    img_find_path = "img.jpg"

    img_paths = save_snapshots_from_planes(json_path)
    img1_path, img2_path = img_paths[0], img_paths[1]

    # Show the snapshots in windows
    show_image_cv2(img1_path, "Primary Face Snapshot")
    show_image_cv2(img2_path, "Opposite Face Snapshot")

    img_find = cv2.imread(img_find_path)
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)

    # Align and show for primary face
    angle_deg1, mean_2d1, scale_2d1,error1 = align_and_show(img_find, img1)
    print(error1)

    # Align and show for opposite face
    angle_deg2, mean_2d2, scale_2d2,error2 = align_and_show(img_find, img2)
    print(error2)

    if error1>error2:
    # Show final aligned mesh for both (optional)
        show_final_aligned_mesh(json_path, angle_deg2, mean_2d2, scale_2d2)
    else:
        show_final_aligned_mesh(json_path, angle_deg1, mean_2d1, scale_2d1)
