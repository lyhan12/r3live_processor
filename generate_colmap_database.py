import argparse
import pycolmap
import os

def main():
    parser = argparse.ArgumentParser(description='Process COLMAP sparse reconstruction')
    parser.add_argument("--model_path", required=True, type=str, help="Path to the input COLMAP model directory")

    args = parser.parse_args()

    model_path = args.model_path
    db_path = os.path.join(model_path, "database.db")

    if not os.path.exists(model_path):
        print(f"Input path '{model_path}' does not exist.")
        return

    if os.path.exists(db_path):
        response = input(f"Database file '{db_path}' already exists. Do you want to remove it? (y/n): ").strip().lower()
        if response == 'y':
            os.remove(db_path)
            print(f"Removed existing database file '{db_path}'.")
        else:
            print("Operation aborted by user.")
            return

    # Load the input COLMAP model
    model = pycolmap.Reconstruction(model_path)

    # Create a new database
    database = pycolmap.Database(db_path)

    # Add cameras
    for _, camera in model.cameras.items():
        database.write_camera(camera, True)

    # Add images and keypoints
    for _, image in model.images.items():
        database.write_image(image, True)

    # Close the database
    database.close()

    print(f"Database created at '{db_path}'")

if __name__ == '__main__':
    main()

