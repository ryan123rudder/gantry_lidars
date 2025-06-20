import yaml
import numpy as np
from scipy.spatial.transform import Rotation as R
import subprocess
import sys
import os

def run_static_tf_from_yaml(yaml_path, parent_frame='base_link'):
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    # Extract transform
    T = np.array(data['Transform']['T']).flatten()
    R_matrix = np.array(data['Transform']['R'])
    rotation = R.from_matrix(R_matrix)
    roll, pitch, yaw = rotation.as_euler('xyz', degrees=False)

    # Infer child frame from file name
    fname = os.path.basename(yaml_path).lower()
    if 'east' in fname:
        child_frame = 'l515_east_depth_optical_frame'
    elif 'west' in fname:
        child_frame = 'l515_west_depth_optical_frame'
    elif 'center' in fname:
        child_frame = 'l515_center_depth_optical_frame'
    else:
        print(f"Could not determine child frame from filename '{fname}'")
        return

    args = [str(x) for x in [*T, roll, pitch, yaw, parent_frame, child_frame]]
    print("ros2 run tf2_ros static_transform_publisher", " ".join(args))

    #subprocess.Popen(['ros2', 'run', 'tf2_ros', 'static_transform_publisher', *args])

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 yaml_to_static_tf.py <yaml_file1> <yaml_file2> ...")
        sys.exit(1)

    for path in sys.argv[1:]:
        run_static_tf_from_yaml(path)
