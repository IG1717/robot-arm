# Robot Arm

## Current Progress:
Added a mock robot description from claude to test ROS setup

## Run
```bash
cd ros_ws && pixi shell
colcon build --symlink-install
source install/setup.zsh
ros2 launch arm_description display.launch.py
```

## Reference
RoboStack Setup : https://robostack.github.io/GettingStarted.html