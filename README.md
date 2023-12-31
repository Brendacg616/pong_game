# Pong Game 

Single player pong game controlled using computer vision

## Dependencies
### OpenCV 
Installed from source following these instructions:
https://www.geeksforgeeks.org/how-to-install-opencv-in-c-on-linux/

### OpenCV extra modules 
For Aruco Marker detection 
Installed from source:
https://github.com/opencv/opencv_contrib

### PySDL2
Install by running the following command on a terminal
` pip install -U pysdl2 `

## Play the game 
1. Clone this repo in your ROS workspace and compile using catkin_make
2. Print the ArUco marker that is included on this repo.
3. Run roslaunch file on a terminal:
` roslaunch pong_game pong_launch.launch `
4. Move the ArUco Marker up and down to control your racket.
5. Enjoy! :)
