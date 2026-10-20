"""Show the arm in RViz with a slider for every joint.

    ros2 launch arm_description display.launch.py
    ros2 launch arm_description display.launch.py gui:=false   # no sliders
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare("arm_description")

    model_arg = DeclareLaunchArgument(
        "model",
        default_value=PathJoinSubstitution([pkg_share, "urdf", "arm.urdf.xacro"]),
        description="Path to the robot xacro file",
    )
    gui_arg = DeclareLaunchArgument(
        "gui", default_value="true", description="Show joint sliders"
    )
    rviz_arg = DeclareLaunchArgument(
        "rviz_config",
        default_value=PathJoinSubstitution([pkg_share, "rviz", "display.rviz"]),
        description="RViz config file",
    )

    robot_description = ParameterValue(
        Command(["xacro ", LaunchConfiguration("model")]), value_type=str
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{"robot_description": robot_description}],
    )

    joint_state_publisher_gui = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        condition=IfCondition(LaunchConfiguration("gui")),
    )

    joint_state_publisher = Node(
        package="joint_state_publisher",
        executable="joint_state_publisher",
        condition=UnlessCondition(LaunchConfiguration("gui")),
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", LaunchConfiguration("rviz_config")],
        output="screen",
    )

    return LaunchDescription(
        [
            model_arg,
            gui_arg,
            rviz_arg,
            robot_state_publisher,
            joint_state_publisher_gui,
            joint_state_publisher,
            rviz,
        ]
    )
