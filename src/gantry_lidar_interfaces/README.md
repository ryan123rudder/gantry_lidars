Capture:
    Parameters
    - outname: string name of the output file. Preppended to timestamp.
    - sensors: list of string names of sensors to collect (like "l515_center")
    - duration: float32, how long to capture for.
    `ros2 service call /gantry_capture_service/capture gantry_lidar_interfaces/srv/Capture "{outname: 'name', sensors: ['l515_center'], duration: 10.0}"`
Download:
    Parameters
    - name: string name of the file to download. Must be exact (with timestamp)
    `ros2 service call /gantry_capture_service/download/name gantry_lidar_interfaces/srv/DownloadName "{name: 'name'}"`
Delete:
    - name: string name of the file to delete. Must be exact (with timestamp)
    `ros2 service call /gantry_capture_service/delete/name gantry_lidar_interfaces/srv/DeleteName "{name: 'name'}"`