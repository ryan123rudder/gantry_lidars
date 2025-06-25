import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
from gantry_services.srv import String
import subprocess # For running ROS bag commands
import signal # For sending shutdown sig
import shutil

from datetime import datetime # For parsing by time range

import json
import time

DATA_DIR = "~/RoSE_Bags"
TIME_STR = "%Y-%m-%dT%H-%M-%S"

def start_http_server(self):
    subprocess.Popen([
        "python3", "-m", "http.server", "8000",
        "--directory", str(DATA_DIR),
        "--bind", "0.0.0.0"
    ])

def parse_time(timestr):
        return datetime.strptime(timestr, TIME_STR)

class GantryCaptureService(Node):
    def __init__(self):
        super().__init__('gantry_capture_service')

        # Info
        self.create_service(Trigger, 'info', self.info_callback)
        
        # Capture sensor data
        self.create_service(String, 'capture', self.capture_callback)

        # Download
        self.create_service(String, 'download/name', self.download_name_callback)
        self.create_service(String, 'download/timeRange', self.download_time_range_callback)

        # Delete
        self.create_service(String, 'delete/name', self.delete_name_callback)
        self.create_service(String, 'delete/timeRange', self.delete_time_range_callback)
        
        # Start HTTP server
        self.start_http_server()

        self.get_logger().info("Gantry capture service running")

    def info_callback(self, request, response):
        response.success = True
        response.message = "idk what to put here"
        return response

    def capture_callback(self, request, response):
        """
        Capture a bag for a set time and saves it locally, zipped
        Service Arguments
        - duration: how long to capture for
        - sensors: list of str names of sensors
        - outname: name of bag to save. bag will be saved as "outname_timestamp"
        """
        try:
            req_data = json.loads(request.data)
            duration = req_data.get("duration", 10.0)
            sensors = req_data.get("sensors", [])
            outname = req_data.get("outname", "")

            # Match directories like: "outname_*"
            matches = list(DATA_DIR.glob(f"{outname}_*"))
            
            # If file exists 
            if matches:
                self.get_logger().info(f"Filename already exists: {self.outname}")
                response.data = json.dumps({"status": "ERROR", "reason": "filename already exists"})
                return response
            
            # Format filename
            timestamp = datetime.now().strftime(TIME_STR)
            self.filename = f"{outname}_{timestamp}"

            # Set Topics
            for sensor in sensors:
                if sensor == "l515_center" or sensor == "l515_west" or sensor == "l515_east":
                    topics += "/"+sensor+"/depth/color/points"

            # Capture Bag
            self.get_logger().info(f"Capturing data: {duration}s from {sensors}, output: {outname}")
            cmd = ['ros2', 'bag', 'record', '-o', self.filename] + topics
            self.record_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.get_logger().info(f"Started recording bag: {self.filename}")

            time.sleep(duration) # Delay

            # End capture
            self.record_process.send_signal(signal.SIGINT)
            self.record_process.wait()
            self.record_process = None

            self.get_logger().info(f"Stopped recording bag: {self.filename}")
           
            # Zip bag
            self.get_logger().info(f"Making .zip archive: {self.filename}.zip")
            shutil.make_archive(self.filename, 'zip', DATA_DIR / self.filename)

            # Delete original folder
            self.get_logger().info(f"Deleting original: {self.filename}")
            shutil.rmtree(DATA_DIR / self.filename)

            response.data = json.dumps({
                "status": "ACK",
                "duration": duration,
                "sensors": sensors,
                "outname": outname
            })

        except Exception as e:
            response.data = json.dumps({"status": "ERROR", "reason": str(e)})
        return response
    
    def download_name_callback(self, request, response):
        """
        Download bags by name. All bags with matching name will be downloaded (although there should only be one)
        """
        try:
            data = json.loads(request.data)
            outname = data.get("name")

            # Get matches (Should only have one)
            matches = sorted(DATA_DIR.glob(f"{outname}_*"), reverse=True)
            if not matches:
                response.data = json.dumps({"success": False, "error": "Not found"})
                return response

            # Figure out what the http path to the zip is
            folder = matches[0].name
            ip = self.get_ip()
            url = f"http://{ip}:8000/{folder}.zip"

            # Return the zip path for wget by client
            response.data = json.dumps({
                "success": True,
                "url": url
            })

        except Exception as e:
            response.data = json.dumps({"success": False, "error": str(e)})
        return response

    def download_time_range_callback(self, request, response):
        """
        Download bags by time range. All bags between start and end will be downloaded.
        Time stamp should be formated like "yyyy-mm-ddThh-mm-ss" in 24hr time
        """
        try:
            data = json.loads(request.data)
            start = data.get("start")
            end = data.get("end")
            # EXECUTE DOWNLOAD (DO THIS IN A BATCH, ZIP ZIPs TOGETHER)
            response.data = f"Downloaded files from {start} to {end}"
        except Exception as e:
            response.data = f"Error parsing request: {str(e)}"
        return response

    def delete_name_callback(self, request, response):
        """
        Delete bags by name. All bags with matching name will be deleted (although there should only be one)
        """
        try:
            data = json.loads(request.data)
            outname = data.get("name")
            if outname == "":
                self.get_logger().info(f"Must delete a named file if deleting by name. Delete by time range instead.")
                response.data = json.dumps({"status": "ERROR", "reason": "Can't delete unnamed file. Delete by time range instead."})
                return response
            # Match directories like: "outname_*"
            matches = list(DATA_DIR.glob(f"{outname}_*"))
            
            # No matches
            if not matches:
                response.data = json.dumps({
                    "success": False,
                    "error": f"No bag found with name '{outname}'"
                })
                return response

            # Get list of files to be deleted (should only be one)
            deleted = []
            for path in matches:
                if path.is_dir():
                    shutil.rmtree(path)
                    deleted.append(path.name)

            response.data = json.dumps({
                "success": True,
                "deleted": deleted
            })

        except Exception as e:
            response.data = json.dumps({"success": False, "error": str(e)})
        return response



    def delete_time_range_callback(self, request, response):
        """
        Delete bags by time range. All bags between start and end will be deleted.
        Time stamp should be formated like yyyy-mm-ddThh-mm-ss" in 24hr time
        """
        try:
            data = json.loads(request.data)
            start = datetime.strptime(data["start"], TIME_STR)
            end = datetime.strptime(data["end"], TIME_STR)

            deleted = []
            for path in DATA_DIR.iterdir():
                if not path.is_dir():
                    continue
                try:
                    # Extract timestamp from last underscore
                    ts_str = path.name.split('_')[-1]
                    ts = datetime.strptime(ts_str, TIME_STR)
                    if start <= ts <= end:
                        shutil.rmtree(path)
                        deleted.append(path.name)
                except Exception:
                    continue

            response.data = json.dumps({
                "success": True,
                "deleted": deleted
            })

        except Exception as e:
            response.data = json.dumps({"success": False, "error": str(e)})
        return response


def main(args=None):
    rclpy.init(args=args)
    node = GantryCaptureService()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
