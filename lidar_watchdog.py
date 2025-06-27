#!/usr/bin/env python3
import os
import signal
import subprocess
import threading
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2

# Adjust these to match your package and launch file
PACKAGE_NAME = 'my_package'
LAUNCH_FILE = 'multi_l515.launch.py'

# How long (in seconds) to tolerate a silent camera before reset
STALE_TIMEOUT = 2.0

# Camera topic map
CAMERAS = {
    'l515_center': {'topic': '/l515_center/depth/color/points', 'last_msg': None},
    'l515_west':   {'topic': '/l515_west/depth/color/points',   'last_msg': None},
    'l515_east':   {'topic': '/l515_east/depth/color/points',   'last_msg': None},
}

# def spawn_launch():
#     """Start the ROS2 launch file as a subprocess."""
#     cmd = ['ros2', 'launch', PACKAGE_NAME, LAUNCH_FILE]
#     # start in its own process group so we can kill all children if needed
#     return subprocess.Popen(cmd, preexec_fn=os.setsid)

class TopicMonitor(Node):
    def __init__(self):
        super().__init__('l515_topic_watchdog')
        for name, cfg in CAMERAS.items():
            self.create_subscription(
                PointCloud2, cfg['topic'], self._make_cb(name), 10
            )
        self.timer = self.create_timer(1.0, self.check_stale)

    def _make_cb(self, cam_name):
        def cb(msg):
            CAMERAS[cam_name]['last_msg'] = self.get_clock().now()
        return cb

    def check_stale(self):
        now = self.get_clock().now()
        for name, cfg in CAMERAS.items():
            last = cfg['last_msg']
            # if we've never seen a message, or it's older than our threshold:
            if last is None or (now - last).nanoseconds * 1e-9 > STALE_TIMEOUT:
                self.get_logger().error(f"Stale LiDAR '{name}' – resetting node")
                # kill that node’s process by name
                # assumes the process command-line contains "--ros-args __node:=<name>"
                os.system(f"pkill -f \"--ros-args.*__node:={name}\"")
                # reset its timestamp so we don’t repeatedly kill in a loop
                CAMERAS[name]['last_msg'] = now

def main():
    # Initialize ROS2 and start monitoring topics
    rclpy.init()
    mon = TopicMonitor()

    try:
        rclpy.spin(mon)
    except KeyboardInterrupt:
        pass
    finally:
        # cleanup
        mon.get_logger().info("Shutting down watchdog and launch")
        rclpy.shutdown()

if __name__ == '__main__':
    main()
