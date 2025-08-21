import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import KDTree

# --- Step 1: Load and sample contours ---
def get_best_contour(img_path, n_points=200):
    img = cv2.imread(img_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    contour = contours[1] if len(contours) >= 2 else contours[0]
    contour = contour[:, 0, :].astype(np.float32)
    indices = np.linspace(0, len(contour) - 1, n_points, endpoint=False).astype(int)
    return contour[indices]

# --- Step 2: Normalize scale ---
def normalize_scale(points):
    mean = np.mean(points, axis=0)
    centered = points - mean
    scale = np.linalg.norm(centered)
    return centered / scale, mean, scale

# --- Step 3: PCA orientation ---
def pca_angle(points):
    cov = np.cov(points.T)
    eigvals, eigvecs = np.linalg.eig(cov)
    dominant = eigvecs[:, np.argmax(eigvals)]
    return np.degrees(np.arctan2(dominant[1], dominant[0]))

def rotate(points, angle_deg):
    rad = np.radians(angle_deg)
    rot = np.array([[np.cos(rad), -np.sin(rad)], [np.sin(rad), np.cos(rad)]])
    return points @ rot.T

# --- Step 4: ICP refinement ---
def icp_2d(source, target, max_iter=50, tolerance=1e-6):
    src = source.copy()
    tgt = target.copy()
    prev_error = float("inf")
    for _ in range(max_iter):
        tree = KDTree(tgt)
        distances, indices = tree.query(src)
        matched = tgt[indices]
        src_mean = np.mean(src, axis=0)
        tgt_mean = np.mean(matched, axis=0)
        src_centered = src - src_mean
        tgt_centered = matched - tgt_mean
        H = src_centered.T @ tgt_centered
        U, _, Vt = np.linalg.svd(H)
        R = Vt.T @ U.T
        if np.linalg.det(R) < 0:
            Vt[-1] *= -1
            R = Vt.T @ U.T
        t = tgt_mean - R @ src_mean
        src = (R @ src.T).T + t
        error = np.mean(distances)
        if abs(prev_error - error) < tolerance:
            break
        prev_error = error
    return src, R, t, error

# --- Step 5: Try flip variants ---
def align_with_reflection_check_all(source, target):
    flips = {
        "no_flip": source,
        "horizontal": source * [-1, 1],
        "vertical": source * [1, -1],
        "both": source * [-1, -1],
    }
    best_result, best_error = None, float("inf")
    for label, variant in flips.items():
        aligned, _, _, error = icp_2d(variant, target)
        #print(f"{label:<10} ICP error: {error:.4f}")
        if error < best_error:
            best_result = aligned
            best_error = error
    return best_result

# --- Step 6: Plotting utility ---
def plot_contours(pts_red, pts_blue, title):
    plt.figure(figsize=(6, 6))
    plt.plot(pts_red[:, 0], pts_red[:, 1], color='red', linewidth=2, label='2D image contour')
    plt.plot(pts_blue[:, 0], pts_blue[:, 1], color='blue', linewidth=2, linestyle='--', label='3D model contour')
    plt.scatter(pts_red[:, 0], pts_red[:, 1], color='red', s=10)
    plt.scatter(pts_blue[:, 0], pts_blue[:, 1], color='blue', s=10)
    plt.legend()
    plt.axis('equal')
    plt.gca().invert_yaxis()
    plt.grid(True)
    plt.title(title)
    plt.tight_layout()
    plt.show()

# --- Main Execution ---
if __name__ == "__main__":
    contour_2d = get_best_contour("img1.jpg")
    contour_3d = get_best_contour("img2.jpg")

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
