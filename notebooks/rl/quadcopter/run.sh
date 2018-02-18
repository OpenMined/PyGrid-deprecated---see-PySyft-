#!/bin/bash -e

#source activate root
cd ~/catkin_ws
source devel/setup.bash
cd src/RL-Quadcopter/quad_controller_rl/launch
roslaunch quad_controller_rl rl_controller.launch
