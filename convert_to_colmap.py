import os
import sqlite3
import struct
import shutil
import argparse
from scipy.spatial.transform import Rotation as R

def create_connection(db_file):
    """Create a database connection to the SQLite database specified by db_file."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Exception as e:
        print(e)
    return conn

def create_tables(conn):
    """Create tables in the database."""
    sql_create_images_table = """CREATE TABLE IF NOT EXISTS images (
                                    image_id INTEGER PRIMARY KEY,
                                    name TEXT NOT NULL,
                                    camera_id INTEGER,
                                    prior_qw REAL,
                                    prior_qx REAL,
                                    prior_qy REAL,
                                    prior_qz REAL,
                                    prior_tx REAL,
                                    prior_ty REAL,
                                    prior_tz REAL,
                                    FOREIGN KEY (camera_id) REFERENCES cameras (camera_id)
                                );"""
    sql_create_cameras_table = """CREATE TABLE IF NOT EXISTS cameras (
                                    camera_id INTEGER PRIMARY KEY,
                                    model INTEGER NOT NULL,
                                    width INTEGER NOT NULL,
                                    height INTEGER NOT NULL,
                                    params BLOB NOT NULL,
                                    prior_focal_length INTEGER
                                );"""
    try:
        cursor = conn.cursor()
        cursor.execute(sql_create_images_table)
        cursor.execute(sql_create_cameras_table)
    except Exception as e:
        print(e)

def insert_camera(conn, camera_id, model, width, height, params, prior_focal_length):
    """Insert a new camera into the cameras table."""
    # Pack parameters into a binary blob
    params_blob = struct.pack(f'{"d" * len(params)}', *params)
        
    sql = '''INSERT INTO cameras(camera_id, model, width, height, params, prior_focal_length)
             VALUES(?,?,?,?,?,?)'''
    cursor = conn.cursor()
    cursor.execute(sql, (camera_id, model, width, height, params_blob, prior_focal_length))

def insert_image(conn, image_data):
    """Insert a new image into the images table."""
    sql = '''INSERT INTO images(image_id, name, camera_id, prior_qw, prior_qx, prior_qy, prior_qz, prior_tx, prior_ty, prior_tz)
             VALUES(?,?,?,?,?,?,?,?,?,?)'''
    cursor = conn.cursor()
    cursor.execute(sql, image_data)

def parse_image_poses(file_path):
    image_poses = {}
    with open(file_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            image = parts[0]
            pose = list(map(float, parts[1:]))
            image_poses[image] = pose
    return image_poses

def invert_pose(tx, ty, tz, qx, qy, qz, qw):
    """Invert the pose given by quaternion and translation."""
    # Invert quaternion
    inv_qw, inv_qx, inv_qy, inv_qz = qw, -qx, -qy, -qz
    # Invert translation
    rotation = R.from_quat([inv_qx, inv_qy, inv_qz, inv_qw])
    inv_t = -rotation.apply([tx, ty, tz])
    return inv_t[0], inv_t[1], inv_t[2], inv_qx, inv_qy, inv_qz, inv_qw

def main():
    parser = argparse.ArgumentParser(description='Convert dataset to COLMAP format')
    parser.add_argument("--data_dir", type=str, required=True, help="Path to the dataset")
    parser.add_argument("--output_name", type=str, help="Name of the output COLMAP directory", default="colmap_data")
    parser.add_argument("--fx", type=float, required=True, help="Focal length in x direction")
    parser.add_argument("--fy", type=float, required=True, help="Focal length in y direction")
    parser.add_argument("--cx", type=float, required=True, help="Principal point x-coordinate")
    parser.add_argument("--cy", type=float, required=True, help="Principal point y-coordinate")
    parser.add_argument("--k1", type=float, required=True)
    parser.add_argument("--k2", type=float, required=True)
    parser.add_argument("--p1", type=float, required=True)
    parser.add_argument("--p2", type=float, required=True)
    parser.add_argument("--w", type=float, required=True, help="Width")
    parser.add_argument("--h", type=float, required=True, help="Height")
    parser.add_argument("--sample_ratio", type=int, default=1, help="Image Sampling Ratio")
    args = parser.parse_args()

    data_dir = args.data_dir
    output_name = args.output_name
    fx = args.fx
    fy = args.fy
    cx = args.cx
    cy = args.cy
    k1 = args.k1
    k2 = args.k2
    p1 = args.p1
    p2 = args.p2
    w = args.w
    h = args.h
    sample_ratio = args.sample_ratio

    print("Processing data folder: ", data_dir)

    colmap_dir = os.path.join(data_dir, output_name)
    if os.path.exists(colmap_dir):
        print("COLMAP directory '{}' already exists. Do you want to remove it? (y/n)".format(colmap_dir))
        choice = input().lower()
        if choice == 'y':
            shutil.rmtree(colmap_dir)

    os.makedirs(colmap_dir, exist_ok=True)

    # Initialize containers for camera and image data
    cameras_data = {}
    images_data = []

    image_dir = os.path.join(data_dir, 'images')
    poses_file = os.path.join(data_dir, 'image_poses.txt')

    image_poses = parse_image_poses(poses_file)

    print("Image Poses: ", len(image_poses.items()))

    for image, pose in image_poses.items():
        image_path = os.path.join(image_dir, image)
        if not os.path.exists(image_path):
            continue

        # Assuming fixed camera parameters for simplicity
        camera_id = 1
        if camera_id not in cameras_data:
            cameras_data[camera_id] = {
                "H": h,  # Example value; replace with actual height
                "W": w,  # Example value; replace with actual width
                "intrinsics": [fx, fy, cx, cy, k1, k2, p1, p2],  # Use provided intrinsics
            }

        image_id = int(image.split('_')[1].split('.')[0])

        if image_id % sample_ratio != 0:
            continue

        # Extract rotation and translation
        tx, ty, tz, qx, qy, qz, qw = pose
        tx, ty, tz, qx, qy, qz, qw = invert_pose(tx, ty, tz, qx, qy, qz, qw)

        image_name = os.path.relpath(image_path, data_dir)
        images_data.append({
            "image_id": image_id,
            "qw": qw,
            "qx": qx,
            "qy": qy,
            "qz": qz,
            "tx": tx,
            "ty": ty,
            "tz": tz,
            "camera_id": camera_id, 
            "name": image_name
        })

    print("Saved colmap model to ", colmap_dir)
    # Write to cameras.txt
    with open(os.path.join(colmap_dir, 'cameras.txt'), 'w') as f:
        f.write("# Camera list with one line of data per camera:\n")
        f.write("#   CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]\n")
        f.write("# Number of cameras: 1\n")
        for camera_id, data in cameras_data.items():
            line = f"{camera_id} OPENCV {data['W']} {data['H']} {' '.join(map(str, data['intrinsics']))}\n"
            f.write(line)

    # Write to images.txt
    with open(os.path.join(colmap_dir, 'images.txt'), 'w') as f:
        f.write("# Image list with two lines of data per image:\n")
        f.write("#   IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME\n")
        f.write("#   POINTS2D[] as (X, Y, POINT3D_ID)\n")

        for image_data in images_data:
            line = f"{image_data['image_id']} {image_data['qw']} {image_data['qx']} {image_data['qy']} {image_data['qz']} {image_data['tx']} {image_data['ty']} {image_data['tz']} {image_data['camera_id']} {image_data['name']}\n"
            f.write(line)
            f.write("\n")

    # Create an empty points3D.txt in colmap directory
    with open(os.path.join(colmap_dir, 'points3D.txt'), 'w') as f:
        f.write("# 3D point list with one line of data per point:\n")
        f.write("#   POINT3D_ID, X, Y, Z, R, G, B, ERROR, TRACK[] as (IMAGE_ID, POINT2D_IDX)\n")
        f.write("# Number of points: 0\n")

    with open(os.path.join(colmap_dir, 'image_list.txt'), 'w') as f:
        for image_data in images_data:
            f.write(f"{image_data['name']}\n")

    # Database file path
    database_path = os.path.join(colmap_dir, 'database.db')
    print("Saved database to", database_path)

    # Create and connect to the database
    conn = create_connection(database_path)
    if conn is not None:
        create_tables(conn)

        # Start a single transaction
        conn.execute('BEGIN')

        # Example usage
        camera_id = 1
        model = 4  # Assuming 1 represents PINHOLE
        width = cameras_data[camera_id]["W"]
        height = cameras_data[camera_id]["H"]
        params = cameras_data[camera_id]["intrinsics"]  # Already a list
        prior_focal_length = -1

        insert_camera(conn, camera_id, model, width, height, params, prior_focal_length)

        for image_data in images_data:
            # Image data to insert
            img_data = (image_data["image_id"], image_data["name"], camera_id, 
                        image_data["qw"], image_data["qx"], image_data["qy"], image_data["qz"], 
                        image_data["tx"], image_data["ty"], image_data["tz"])
            insert_image(conn, img_data)

        # Commit the transaction
        conn.commit()
        conn.close()
    else:
        print("Error! Cannot create the database connection.")        

if __name__ == "__main__":
    main()

