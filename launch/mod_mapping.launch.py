import os.path

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.conditions import IfCondition

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    package_path = get_package_share_directory('fast_lio')
    default_config_path = os.path.join(package_path, 'config')
    default_rviz_config_path = os.path.join(
        package_path, 'rviz', 'fastlio.rviz')

    use_sim_time = LaunchConfiguration('use_sim_time')
    config_path = LaunchConfiguration('config_path')
    config_file = LaunchConfiguration('config_file')
    rviz_use = LaunchConfiguration('rviz')
    rviz_cfg = LaunchConfiguration('rviz_cfg')
    export_map = LaunchConfiguration('export_map')
    map_output_dir = LaunchConfiguration('map_output_dir')
    map_export_idle_seconds = LaunchConfiguration('map_export_idle_seconds')
    map_resolution = LaunchConfiguration('map_resolution')

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time', default_value='false',
        description='Use simulation (Gazebo) clock if true'
    )
    declare_config_path_cmd = DeclareLaunchArgument(
        'config_path', default_value=default_config_path,
        description='Yaml config file path'
    )
    declare_config_file_cmd = DeclareLaunchArgument(
        'config_file', default_value='mid360.yaml',
        description='Config file'
    )
    declare_rviz_cmd = DeclareLaunchArgument(
        'rviz', default_value='true',
        description='Use RViz to monitor results'
    )
    declare_rviz_config_path_cmd = DeclareLaunchArgument(
        'rviz_cfg', default_value=default_rviz_config_path,
        description='RViz config file path'
    )
    declare_export_map_cmd = DeclareLaunchArgument(
        'export_map', default_value='true',
        description='Save the colored 2.5D RViz map as a PCD and standalone HTML editor'
    )
    declare_map_output_dir_cmd = DeclareLaunchArgument(
        'map_output_dir', default_value=os.path.join(os.getcwd(), 'maps'),
        description='Output directory; each mapping run gets its own subdirectory'
    )
    declare_map_export_idle_seconds_cmd = DeclareLaunchArgument(
        'map_export_idle_seconds', default_value='3.0',
        description='Export after this many seconds without map updates; 0 disables idle export'
    )
    declare_map_resolution_cmd = DeclareLaunchArgument(
        'map_resolution', default_value='0.2',
        description='2.5D cell size in meters, shared by lio_post and the HTML display'
    )

    fast_lio_node = Node(
        package='fast_lio',
        executable='fastlio_mapping',
        parameters=[PathJoinSubstitution([config_path, config_file]),
                    {'use_sim_time': use_sim_time,
                     # Select the existing Livox CustomMsg subscriber.
                     'preprocess.lidar_type': 1}],
        output='screen'
    )
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        parameters=[{'use_sim_time': use_sim_time}],
        arguments=['-d', rviz_cfg],
        condition=IfCondition(rviz_use)
    )
    
    mod_explore_node = Node(
        package='mod_explore_cpp',
        executable='lio_post',
        parameters=[{'use_sim_time': use_sim_time,
                     'update_range_xy': 6.0,
                     'map_resolution': ParameterValue(map_resolution, value_type=float),
                     'mavros_pose_topic': '/follower/mavros/local_position/pose'}],
        output='screen'
    )
    map_recorder_node = Node(
        package='mod_explore',
        executable='map_recorder',
        parameters=[{'use_sim_time': use_sim_time,
                     'cloud_topic': '/explore_map_color',
                     'cell_size': ParameterValue(map_resolution, value_type=float),
                     'output_dir': ParameterValue(map_output_dir, value_type=str),
                     'idle_seconds': ParameterValue(map_export_idle_seconds, value_type=float)}],
        condition=IfCondition(export_map),
        # Allow full-resolution PCD and HTML writes to finish on Ctrl-C.
        sigterm_timeout='120',
        output='screen'
    )

    ld = LaunchDescription()
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_config_path_cmd)
    ld.add_action(declare_config_file_cmd)
    ld.add_action(declare_rviz_cmd)
    ld.add_action(declare_rviz_config_path_cmd)
    ld.add_action(declare_export_map_cmd)
    ld.add_action(declare_map_output_dir_cmd)
    ld.add_action(declare_map_export_idle_seconds_cmd)
    ld.add_action(declare_map_resolution_cmd)

    ld.add_action(map_recorder_node)
    ld.add_action(fast_lio_node)
    ld.add_action(rviz_node)
    ld.add_action(mod_explore_node)

    return ld
