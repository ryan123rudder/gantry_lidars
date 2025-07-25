from setuptools import find_packages, setup

package_name = 'gantry_lidars'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='gantry_lattepanda',
    maintainer_email='ryanmanley@mines.edu',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
		'gantry_lidars = gantry_lidars.PointCloudMerger:main'
        'lidar_watchdog = gantry_lidars.lidar_watchdog:main'
        ],
    },
)
