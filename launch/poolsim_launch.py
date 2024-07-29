from os import environ

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, ExecuteProcess, Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def launch_gz(context, *args, **kwargs):
    """
    Launch the gz sim.
    """

    env = {'GZ_SIM_SYSTEM_PLUGIN_PATH':
           ':'.join([environ.get('GZ_SIM_SYSTEM_PLUGIN_PATH', default=''),
                     environ.get('LD_LIBRARY_PATH', default='')]),
           'IGN_GAZEBO_SYSTEM_PLUGIN_PATH':  # TODO(CH3): To support pre-garden. Deprecated.
                      ':'.join([environ.get('IGN_GAZEBO_SYSTEM_PLUGIN_PATH', default=''),
                                environ.get('LD_LIBRARY_PATH', default='')])}

    gz_args = LaunchConfiguration('gz_args').perform(context)
    gz_version = LaunchConfiguration('gz_version').perform(context)
    ign_args = LaunchConfiguration('ign_args').perform(context)
    ign_version = LaunchConfiguration('ign_version').perform(context)
    debugger = LaunchConfiguration('debugger').perform(context)
    on_exit_shutdown = LaunchConfiguration('on_exit_shutdown').perform(context)

    if not len(gz_args) and len(ign_args):
        print("ign_args is deprecated, migrate to gz_args!")
        exec_args = ign_args
    else:
        exec_args = gz_args

    exec = 'ruby $(which gz) sim'

    if debugger != 'false':
        debug_prefix = 'x-terminal-emulator -e gdb -ex run --args'
    else:
        debug_prefix = None

    if on_exit_shutdown:
        on_exit = Shutdown()
    else:
        on_exit = None

    return [ExecuteProcess(
            cmd=[exec, exec_args, '--force-version', gz_version],
            output='screen',
            additional_env=env,
            shell=True,
            prefix=debug_prefix,
            on_exit=on_exit
        )]

def generate_launch_description():
    """
    Generate the launch description for the launch file.
    """

    sim = 'bluerov2_camera.world'
    path = f'~/gazebo_bluerov2/worlds/{sim}'
    path = sim
    print(path)

    gz_args = DeclareLaunchArgument(
        'gz_args', 
        default_value=f'{path} -r -s',
        description='gz sim args'
    )

    gz_version = DeclareLaunchArgument(
        'gz_version',
        default_value='8',
        description='gz sim major version'
    )

    ign_args = DeclareLaunchArgument(
        'ign_args', 
        default_value='',
        description='deprecated: gz sim args'
    )

    ign_version = DeclareLaunchArgument(
        'ign_version',
        default_value='8',
        description='deprecated: gz sim major version'
    )

    debugger = DeclareLaunchArgument(
        'debugger',
        default_value='false',
        description='run in debugger'
    )

    on_exit_shutdown = DeclareLaunchArgument(
        'on_exit_shutdown',
        default_value='false',
        description='shutdown on gz sim exit'
    )

    rosmav_node = Node(
        package="rosmav",
        executable="ros_bluerov2_interface",
        name="bluerov2_interface",
        namespace=""
    )

    image_bridge_node = Node(
        package='ros_gz_image',
        executable='image_bridge',
        name='bluerov2_image_bridge',
        namespace='',
        arguments=['/camera'],
        remappings=[
            ('/camera', '/bluerov2/camera'),
            ('/camera/compressed', 'bluerov2/camera/compressed'),
            ('/camera/compressedDepth', 'bluerov2/camera/compressedDepth'),
            ('/camera/theora', 'bluerov2/camera/theora'),
            ('/camera/zstd', 'bluerov2/camera/zstd'),
        ]
    )

    ld = LaunchDescription()

    ld.add_action(gz_args)
    ld.add_action(gz_version)
    ld.add_action(ign_args)
    ld.add_action(ign_version)
    ld.add_action(debugger)
    ld.add_action(on_exit_shutdown)

    ld.add_action(rosmav_node)
    ld.add_action(image_bridge_node)

    ld.add_action(OpaqueFunction(function=launch_gz))

    return ld
