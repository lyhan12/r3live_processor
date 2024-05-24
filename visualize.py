import numpy as np
import open3d as o3d
import argparse

def read_camera_poses(file_path):
    poses = []
    with open(file_path, 'r') as file:
        for line in file:
            parts = line.strip().split()
            if len(parts) == 8:
                position = np.array(parts[1:4], dtype=np.float64)
                orientation = np.array(parts[4:8], dtype=np.float64)  # Assuming quaternion format
                poses.append((position, orientation))
    return poses

def quaternion_to_rotation_matrix(quaternion):
    return o3d.geometry.get_rotation_matrix_from_quaternion(quaternion)

def create_camera_visualization(pose, size=0.1):
    position, quaternion = pose
    rotation_matrix = quaternion_to_rotation_matrix(quaternion)
    camera = o3d.geometry.TriangleMesh.create_coordinate_frame(size=size)
    camera.translate(position)
    camera.rotate(rotation_matrix, center=position)
    return camera

def load_geometry(file_path):
    if file_path.endswith('.pcd'):
        return o3d.io.read_point_cloud(file_path)
    elif file_path.endswith('.ply'):
        try:
            # Try loading as a mesh first
            return o3d.io.read_triangle_mesh(file_path)
        except Exception:
            # If fails, try loading as a point cloud
            return o3d.io.read_point_cloud(file_path)
    else:
        raise ValueError("Unsupported file format. Only .pcd and .ply are supported.")

def main(camera_file_path, geometry_file_path):
    # Read poses from file
    poses = read_camera_poses(camera_file_path)

    # Load geometry (point cloud or mesh)
    geometry = load_geometry(geometry_file_path)

    # Visualize in Open3D
    vis = o3d.visualization.Visualizer()
    vis.create_window()
    vis.add_geometry(geometry)

    for pose in poses:
        camera_visual = create_camera_visualization(pose)
        vis.add_geometry(camera_visual)

    vis.run()
    vis.destroy_window()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualize camera poses and a geometry (point cloud or mesh) from files.")
    parser.add_argument("camera_file_path", help="Path to the text file containing camera poses.")
    parser.add_argument("geometry_file_path", help="Path to the geometry file (.pcd or .ply).")
    args = parser.parse_args()

    main(args.camera_file_path, args.geometry_file_path)
    

