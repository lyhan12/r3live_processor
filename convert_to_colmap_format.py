import os
import numpy as np
import argparse

def quaternion_to_rotation_matrix(q):
    """Convert a quaternion to a rotation matrix."""
    x, y, z, w = q
    return np.array([
        [1 - 2*y**2 - 2*z**2,     2*x*y - 2*z*w,       2*x*z + 2*y*w],
        [2*x*y + 2*z*w,           1 - 2*x**2 - 2*z**2, 2*y*z - 2*x*w],
        [2*x*z - 2*y*w,           2*y*z + 2*x*w,       1 - 2*x**2 - 2*y**2]
    ])

def convert_to_colmap_format(input_file, output_folder):
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # File paths for output
    images_file = os.path.join(output_folder, 'images.txt')
    points3d_file = os.path.join(output_folder, 'points3D.txt')
    cameras_file = os.path.join(output_folder, 'cameras.txt')

    with open(input_file, 'r') as file:
        lines = file.readlines()

    # Camera parameters from the provided specs
    camera_id = 1
    width, height = 1280, 1024  # Image dimensions
    fx, fy = 863.4241, 863.4171  # Focal lengths
    cx, cy = 640.6808, 518.3392  # Principal point
    k1, k2, p1, p2, k3 = -0.1080, 0.1050, -1.2872e-04, 5.7923e-05, -0.0222  # Distortion coefficients

    with open(cameras_file, 'w') as file:
        file.write(f"{camera_id} PINHOLE {width} {height} {fx} {fy} {cx} {cy}\n")

    with open(images_file, 'w') as file:
        image_id = 0
        for line in lines:
            parts = line.split()
            image_name = parts[0]
            translation = np.array(parts[1:4], dtype=float)
            quaternion = np.array(parts[4:], dtype=float) # x, y, z, w
            rotation_matrix = quaternion_to_rotation_matrix(quaternion)
            camera_center = -np.dot(rotation_matrix.T, translation)  # -R^T * t

            image_id += 1
            if image_id % 5 == 0:
                file.write(f"{image_id} {quaternion[3]} {-quaternion[0]} {-quaternion[1]} {-quaternion[2]} "
                           f"{camera_center[0]} {camera_center[1]} {camera_center[2]} {camera_id} {image_name}\n")
                file.write("\n")  # Empty line for 2D points


    # points3D.txt will be empty as per request
    open(points3d_file, 'w').close()

def main():
    parser = argparse.ArgumentParser(description="Convert image poses to COLMAP format.")
    parser.add_argument("input_file", help="Input file containing image poses.")
    parser.add_argument("output_folder", help="Output folder for the COLMAP files.")
    args = parser.parse_args()

    convert_to_colmap_format(args.input_file, args.output_folder)

if __name__ == "__main__":
    main()

