# Robot Arm Project

## Goal
Build a 5-DOF + gripper desktop robot arm from scratch: 3D-printed PLA parts,
designed in Fusion 360, controlled with ROS 2 (MoveIt 2 + ros2_control), with a
wrist camera. Current phase: software and simulation before buying parts or
detailed CAD.

## Owner
Ilan, mechanical engineering student (Brown), strong in Python and CAD
(Fusion 360, SolidWorks). Prior experience: Teensy 4.1, PlatformIO, NEMA 17
steppers, Raspberry Pi, ROS 2 basics, fusion2urdf.

Explanation preferences: explain math and complex topics in plain English from
scratch (over-explain rather than under-explain); write math as LaTeX.

## Hardware decisions
- **Servos:** 6x Feetech STS3215 12V 30 kg*cm (ST-3215-C018 or C047), plus 1 spare.
  - 45.2 x 24.7 x 35 mm, 55 g, 25T spline, 1:345 gearbox, 12-bit magnetic encoder
  - Stall 30 kg*cm (2.94 N*m); rated continuous 10 kg*cm (0.98 N*m) at 12 V
  - 0.222 s per 60 deg (about 4.7 rad/s); stall current 2.7 A
  - Serial bus (half-duplex TTL, default 1 Mbps), daisy-chained, IDs 0-253
    (factory default ID 1; assign IDs one at a time before chaining)
  - Planned purchase: Seeed (US $22 each) or DFRobot (US $19.90 each)
- **Servo driver:** Waveshare Bus Servo Adapter (A), USB-C to the Pi, 9-12.6 V input
- **Power:** 12 V, 10 A+ supply, inline fuse, kill switch
- **Compute:** Raspberry Pi 5 (owned). It will run Ubuntu 26.04 (needed for Lyrical).
- **Camera:** undecided. Options: RealSense D405 on the wrist (7 cm min range),
  OAK-D Lite as a fixed scene camera, or a Pi camera/webcam with ArUco markers.
- **Shoulder:** GT2 belt reduction, 9 mm reinforced belt, 200 mm closed loop.
  - Leaning 2:1 (20T to 40T, center distance about 69.7 mm): 180 deg range, 1.96 N*m
  - Alternative 3:1 (20T to 60T, center distance about 58.6 mm): 120 deg range only,
    because the servo's absolute encoder covers one turn
  - The joint angle reported to ROS = servo angle / ratio
- **Joints:** servo on one side, bearing on the other (608ZZ or 6802). Base uses a
  6810 thin-section bearing or a lazy-susan bearing.
- **Fasteners:** M3 heat-set inserts and M3 socket head screws

## Kinematics (current placeholder model)
Zero pose: arm pointing straight up (+Z).
| Segment | Length |
|---|---|
| Table to shoulder axis | 110 mm (base 40 + turret 70) |
| Upper arm | 140 mm |
| Forearm | 120 mm |
| Wrist pitch to fingertip | 65 mm (wrist 20 + gripper body 25 + fingers 20) |
| Reach from shoulder axis | 325 mm |

Joints: `base_yaw` (Z, +/-160), `shoulder_pitch` (Y, +/-90 for 2:1),
`elbow_pitch` (Y, +/-140), `wrist_pitch` (Y, +/-100), `wrist_roll` (Z, +/-160),
`gripper_left` (prismatic 0-25 mm), and `gripper_right` (mimics `gripper_left`).

Frames: `tool0` (between the fingertips; MoveIt end effector), `camera_link`
(X = view direction), `camera_optical_frame` (Z forward).

Torque check from the model: shoulder gravity torque with the arm horizontal and
no payload is about 0.99 N*m. The shoulder's effort limit is 1.96 N*m (rated
continuous 0.98 N*m times the 2:1 ratio), which leaves room for about 300 g at
full reach. The URDF divides the shoulder velocity limit by the ratio too.
Masses use 55 g per servo plus PLA estimates (about 1.12 kg total).

## Software environment (macOS, Apple Silicon)
- ROS 2 **Lyrical** via **RoboStack + Pixi** (native, no Docker or VM)
- Pixi workspace: `ros_ws/pixi.toml`. The only channel listed is
  `https://prefix.dev/robostack-lyrical`, but conda-forge packages (Qt, PySide6)
  still resolve and come from prefix.dev/conda-forge
- Base packages: ros-lyrical-desktop, ros-dev-tools
- Always work inside `pixi shell`, then `source install/setup.zsh`
- After `pixi add`, exit and reopen `pixi shell`
- Python in the env is 3.14
- Known fixes already applied:
  - `setuptools<80` pinned: setuptools 80+ breaks `colcon build --symlink-install`
    for ament_python ("option --editable not recognized")
  - `pyside6` added: needed by joint_state_publisher_gui (python_qt_binding)
  - Qt add-ons added: qt6-webengine, qt6-quick3d, qt6-3d, qt6-graphs, qt6-charts,
    qt6-datavis3d, qt6-scxml, qt6-sensors, qt6-networkauth. Why: conda-forge's
    pyside6 has Python wrappers for these Qt modules but only depends on qt6-main.
    On macOS, python_qt_binding loads PySide6 with `fromlist=['*']`, which imports
    every wrapper, so one missing library (first was `libQt6Pdf.6.dylib`) crashes
    joint_state_publisher_gui and every rqt tool. Older pyside6 builds have the
    same problem, so pinning doesn't help. Keep these packages at qt6-main's version.
    Quick check: `python -c "from python_qt_binding.QtCore import Qt"`
  - `ros-lyrical-xacro`, `ros-lyrical-joint-state-publisher(-gui)` added
- Planned, not installed yet: ros-lyrical-moveit, ros-lyrical-ros2-control,
  ros-lyrical-ros2-controllers, ros-lyrical-ros-gz
- Fallback if Gazebo (especially camera rendering) fails on macOS: Ubuntu VM
  (VMware Fusion or Parallels) or Webots
- Moving or renaming a package: delete `build/ install/ log/`, then rebuild

## Repo layout
```
robot-arm/
├── CLAUDE.md
├── README.md
├── .gitignore          # ignores ros_ws/build, install, log, .pixi, and .vscode/
├── cad/
│   └── fusion/         # .f3d milestone exports (empty so far)
│                       # planned: vendor/ (STEP), stl/
└── ros_ws/
    ├── pixi.toml, pixi.lock   # tracked in git
    └── src/
        └── arm_description/   # ament_python
```
Git: track src/, pixi.toml, pixi.lock, CAD exports, docs. Do not track build/,
install/, log/, or .pixi/. Use Git LFS for STEP/STL/F3D. Git LFS is not
installed or set up yet (no .gitattributes); do that before committing any CAD
files. macOS `.DS_Store` files are not ignored yet.

## arm_description package (current state)
- Build type: **ament_python** (chosen to match the fusion2urdf-ros2 exporter)
- `setup.py` installs `urdf/*`, `launch/*.py`, `rviz/*` via data_files. With
  `--symlink-install`, the installed files are symlinks back to src/, so edits to
  existing files take effect without rebuilding. Rebuild after adding a file or
  changing setup.py.
- `urdf/arm.urdf.xacro`: stick-figure placeholder with cylinders and boxes. All
  dimensions, masses, and limits are `xacro:property` values at the top. Has
  inertia macros, visual-only joint hubs, mimic gripper, tool0, and camera frames.
- `launch/display.launch.py`: runs xacro, then robot_state_publisher,
  joint_state_publisher_gui (or joint_state_publisher with gui:=false), and RViz
  with rviz/display.rviz. Works on macOS as of 2026-10-20.
- `rviz/display.rviz`: Fixed Frame base_link, Grid, RobotModel on
  /robot_description, TF
- `package.xml` exec_depends: xacro, robot_state_publisher,
  joint_state_publisher, joint_state_publisher_gui, rviz2, launch, launch_ros

Run:
```bash
cd ros_ws && pixi shell
colcon build --symlink-install
source install/setup.zsh
ros2 launch arm_description display.launch.py
```
Verify reach: `ros2 run tf2_ros tf2_echo base_link tool0`. Expected about
[0, 0, 0.435] at zero pose, and about [0.325, 0, 0.110] with shoulder_pitch at +90 deg.

## Open items (in progress)
1. Add a massless `world` root link with a fixed joint to `base_link` (not in the
   xacro yet). This fixes the KDL warning "root link base_link has an inertia",
   and Gazebo uses it to anchor the arm.

## Next steps
1. MoveIt Setup Assistant on arm_description to generate `arm_moveit_config`
   (ament_cmake). End effector: tool0. Planning group: the 5 arm joints.
   Gripper group: gripper_left.
2. `arm_bringup`: ros2_control with `mock_components/GenericSystem` plus
   joint_trajectory_controller, so MoveIt can plan and execute on a fake arm
3. Build `sts_hardware_interface` (github.com/adityakamath/sts_hardware_interface)
   from source in src/ and test its mock mode. Alternative:
   feetech_ros2_driver. Expect possible fixes for Lyrical and macOS.
4. Gazebo: gravity torque check per joint, simulated wrist camera
5. Write a half-page requirements spec; gather vendor STEP files
6. Order fit-test parts (1 servo, bearings, belt, pulleys); design and print
   the shoulder joint first
7. Skeleton Fusion model, then the fusion2urdf pipeline test, then detailed CAD

## Conventions
- Keep joint and link names stable; MoveIt config depends on them
- Fusion export: export to a scratch folder, then copy the URDF and meshes into
  arm_description. Never export directly over the package (it would overwrite
  launch/ and rviz/). Keep custom additions (tool0, camera, ros2_control) in a
  separate xacro that includes the generated one.
- Fusion model: Z up; don't position joints with Fusion's joint editor dialog
  (fusion2urdf limitation); set real servo mass (55 g) on imported STEP bodies
- Future Python nodes go in their own ament_python packages
  (e.g. arm_perception, arm_tasks)
