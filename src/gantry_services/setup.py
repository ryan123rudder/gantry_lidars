from setuptools import find_packages, setup
from glob import glob

package_name = 'gantry_services'

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
    maintainer_email='mkreed@mines.edu',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
		'gantry_capture_service=gantry_services.GantryCaptureService:main',
        ],
    },
)
