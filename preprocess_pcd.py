import open3d as o3d
import argparse

def downsample_and_filter(input_file, output_file, voxel_size, nb_neighbors, std_ratio):
    # Load the point cloud from the file
    pcd = o3d.io.read_point_cloud(input_file)

    # Remove outliers
    _, ind = pcd.remove_statistical_outlier(nb_neighbors=nb_neighbors, std_ratio=std_ratio)
    filtered_pcd = pcd.select_by_index(ind)

    # Calculate normals
    filtered_pcd.estimate_normals();

    # Downsample the point cloud
    downsampled_pcd = filtered_pcd.voxel_down_sample(voxel_size)

    # Save the processed point cloud to a PLY file
    o3d.io.write_point_cloud(output_file, downsampled_pcd)
    print(f"Processed point cloud saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Process a PCD file and save as a PLY file.")
    parser.add_argument("input_file", help="Input PCD file name.")
    parser.add_argument("output_file", help="Output PLY file name.")
    args = parser.parse_args()

    # Parameters for downsampling and outlier removal
    voxel_size = 0.05  # Adjust as needed
    nb_neighbors = 20  # Adjust as needed
    std_ratio = 2.0    # Adjust as needed

    downsample_and_filter(args.input_file, args.output_file, voxel_size, nb_neighbors, std_ratio)

if __name__ == "__main__":
    main()

