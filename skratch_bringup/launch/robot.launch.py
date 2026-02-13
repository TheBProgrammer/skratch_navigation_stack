#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess
from ament_index_python.packages import get_package_share_directory
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.descriptions import ParameterValue
import xacro


def generate_launch_description():

    robotname = os.getenv('ROBOT_NAME', 'skratch')

    smart_wheel_driver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory("kelo_tulip"), 'launch'),
            '/example_joypad.launch.py'])
    )

   # --- robot_description from xacro ---
    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name="xacro")]),
        " ",
        PathJoinSubstitution([
            FindPackageShare("skratch_description"),
            "gazebo",
            "gazebo_skratch.xacro",
        ]),
        # You can pass xacro args here if needed, e.g.:
        " ", "movable_joints:=true"
    ])

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': ParameterValue(robot_description_content, value_type=str)
        }],
    )


    # --- Encoder → JointState bridge (make sure package/exe names match your build) ---
    # NOTE: Keep 'wheel_names' order aligned with msg.wheels[] order from the driver.
    wheels_bridge = Node(
        package='skratch_bringup',
        executable='wheels_to_joint_states',
        name='wheels_to_joint_states',
        output='screen',
        parameters=[{
            'wheel_names': ['wheel0', 'wheel1', 'wheel3', 'wheel2'],  # adjust if your wheels[] order differs
            'encoders_in_degrees': False,
            'triplet_order': 'LPR'
        }],
    )

    # --- RViz2 with your config ---
    rviz_config_file = os.path.join(
        get_package_share_directory('skratch_description'),
        'config',
        'robot.rviz'
    )
    rviz_cmd = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
    )
    
    # --- Static TF (parent -> child). Usually base_footprint is parent of base_link. ---
    static_transform = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        output="screen",
        # Syntax (ROS 2): x y z yaw pitch roll frame_id child_frame_id
        arguments=["0", "0", "0", "0", "0", "0", "base_footprint", "base_link"]
    )

    

    if robotname == 'skratch':
        print('[INFO] [launch] skratch: loading')
                             
    
    return LaunchDescription([
        smart_wheel_driver,
        wheels_bridge,
        robot_state_publisher,
        rviz_cmd,
        static_transform
    ])