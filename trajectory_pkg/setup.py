from setuptools import setup

package_name = 'trajectory_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='pc',
    maintainer_email='pc@todo.todo',
    description='trajectory package',
    license='MIT',
    entry_points={
        'console_scripts': [
            'processing_node = trajectory_pkg.processing_node:main',
        ],
    },
)