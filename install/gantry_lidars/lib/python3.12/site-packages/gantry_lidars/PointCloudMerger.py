import rclpy
from rclpy.node import Node

from sensor_msgs.msg import PointCloud2
import sensor_msgs_py.point_cloud2 as pc2
from rclpy.time import Time
import tf2_sensor_msgs.tf2_sensor_msgs as tf2_pc2
from geometry_msgs.msg import TransformStamped
from tf_transformations import quaternion_from_euler
from message_filters import Subscriber, ApproximateTimeSynchronizer

import yaml
import numpy as np
from tf_transformations import quaternion_from_matrix

def load_transform(yaml_path):
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    R = np.array(data['Transform']['R'])
    T = data['Transform']['T']
    T_flat = np.array(data['Transform']['T']).flatten()

    # Build a 4x4 transform matrix
    M = np.eye(4)
    M[:3, :3] = R
    M[:3, 3] = [t[0] for t in T]

    q = quaternion_from_matrix(M)
    return T_flat.tolist(), q

class PointCloudMerger(Node):
    def __init__(self):
        super().__init__('pointcloud_merger')

        # Target frame
        self.declare_parameter('target_frame', 'base_link')
        self.target_frame = self.get_parameter('target_frame').value

        # Static transform for second cloud
        self.declare_parameter('cloud2_frame', 'frame2')
        self.cloud2_frame = self.get_parameter('cloud2_frame').value
        t2, q2 = load_transform('L515_East_properties.yaml')

        # Static transform for third cloud
        self.declare_parameter('cloud3_frame', 'frame3')
        self.cloud3_frame = self.get_parameter('cloud3_frame').value
        t3, q3 = load_transform('L515_West_properties.yaml')


        now = self.get_clock().now().to_msg()

        # TransformStamped for cloud2
        self.transform_2 = TransformStamped()
        self.transform_2.header.frame_id = self.target_frame
        self.transform_2.child_frame_id = self.cloud2_frame
        self.transform_2.transform.translation.x = t2[0]
        self.transform_2.transform.translation.y = t2[1]
        self.transform_2.transform.translation.z = t2[2]
        self.transform_2.transform.rotation.x = q2[0]
        self.transform_2.transform.rotation.y = q2[1]
        self.transform_2.transform.rotation.z = q2[2]
        self.transform_2.transform.rotation.w = q2[3]
        self.transform_2.header.stamp = now

        # TransformStamped for cloud3
        self.transform_3 = TransformStamped()
        self.transform_3.header.frame_id = self.target_frame
        self.transform_3.child_frame_id = self.cloud3_frame
        self.transform_3.transform.translation.x = t3[0]
        self.transform_3.transform.translation.y = t3[1]
        self.transform_3.transform.translation.z = t3[2]
        self.transform_3.transform.rotation.x = q3[0]
        self.transform_3.transform.rotation.y = q3[1]
        self.transform_3.transform.rotation.z = q3[2]
        self.transform_3.transform.rotation.w = q3[3]
        self.transform_3.header.stamp = now

        # Subscribers
        self.pc1_sub = Subscriber(self, PointCloud2, '/l515_center/depth/color/points')
        self.pc2_sub = Subscriber(self, PointCloud2, '/l515_east/depth/color/points')
        self.pc3_sub = Subscriber(self, PointCloud2, '/l515_west/depth/color/points')

        # Synchronize 
        self.sync = ApproximateTimeSynchronizer(
            [self.pc1_sub, self.pc2_sub, self.pc3_sub],
            queue_size=10,
            slop=0.1
        )
        self.sync.registerCallback(self.clouds_callback)

        # Publish
        self.publisher = self.create_publisher(PointCloud2, '/cloud_merged', 10)
        self.get_logger().info(f"Started PointCloudMerger")

    def clouds_callback(self, cloud1, cloud2, cloud3):
        """
        Merge three clouds w/ cloud1 assumed in target_frame
        cloud2 and cloud3 transformed with static transforms
        """
        try:
            c1 = cloud1
            # Apply static transforms
            c2 = tf2_pc2.do_transform_cloud(cloud2, self.transform_2)
            c3 = tf2_pc2.do_transform_cloud(cloud3, self.transform_3)

            # Make list of all points
            merged_points = []
            for cloud in (c1, c2, c3):
                merged_points.extend(pc2.read_points(cloud, skip_nans=True))

            # Build merged cloud
            merged = pc2.create_cloud(
                header=c1.header,
                fields=c1.fields,
                points=merged_points
            )
            # Publish
            self.publisher.publish(merged)

        except Exception as e:
            self.get_logger().warn(f"Point Cloud Merge failed: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = PointCloudMerger()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
