"""One command: Gazebo + the Olympus rover + the ROS-Gazebo bridge.

Run:   ros2 launch ~/olympus_ws/rover_sim.launch.py
Stop:  Ctrl-C (stops all three)

Optional:  ros2 launch ~/olympus_ws/rover_sim.launch.py urdf:=/other/path/rover_sim.urdf z:=0.09
"""
import json
import os

from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription,
                            SetEnvironmentVariable, TimerAction)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

HOME = os.path.expanduser("~")
MODELS = os.path.join(HOME, "olympus_ws", "sim_models")
DEFAULT_URDF = os.path.join(MODELS, "rover_sim", "urdf", "rover_sim.urdf")


STEER_JSON = os.path.join(os.path.dirname(DEFAULT_URDF), "rover_steer.json")
STEER_NODE = os.path.join(HOME, "olympus_ws", "goto", "steer_node.py")


def generate_launch_description():
    # steering only if the URDF was built with --steer (that also writes rover_steer.json)
    steer_args, steer_actions = [], []
    if os.path.exists(STEER_JSON):
        for w in json.load(open(STEER_JSON))["wheels"]:
            steer_args.append(f"/model/rover/steer/{w['steer_joint']}@std_msgs/msg/Float64]gz.msgs.Double")
        steer_actions = [ExecuteProcess(cmd=["python3", STEER_NODE, STEER_JSON], output="screen")]
    # so Gazebo finds package://rover_sim/meshes/... (same as the line in ~/.bashrc)
    old = os.environ.get("GZ_SIM_RESOURCE_PATH", "")
    resource_path = MODELS + (":" + old if old else "")

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"])),
        launch_arguments={"gz_args": "-r empty.sdf"}.items())

    spawn = Node(
        package="ros_gz_sim", executable="create", output="screen",
        arguments=["-file", LaunchConfiguration("urdf"), "-name", "rover",
                   "-z", LaunchConfiguration("z")])

    bridge = Node(
        package="ros_gz_bridge", executable="parameter_bridge", output="screen",
        arguments=["/model/rover/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",
                   "/model/rover/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry"] + steer_args)

    return LaunchDescription([
        DeclareLaunchArgument("urdf", default_value=DEFAULT_URDF),
        DeclareLaunchArgument("z", default_value="0.09"),
        SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", resource_path),
        gazebo,
        TimerAction(period=5.0, actions=[spawn]),     # give Gazebo a few seconds to start first
        TimerAction(period=6.0, actions=[bridge] + steer_actions),
    ])
