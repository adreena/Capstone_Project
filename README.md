This is the project repo for the final project of the Udacity Self-Driving Car Nanodegree: Programming a Real Self-Driving Car. For more information about the project, see the project introduction [here](https://classroom.udacity.com/nanodegrees/nd013/parts/6047fe34-d93c-4f50-8336-b70ef10cb4b2/modules/e1a23b06-329a-4684-a717-ad476f0d8dff/lessons/462c933d-9f24-42d3-8bdc-a08a5fc866e4/concepts/5ab4b122-83e6-436d-850f-9f4d26627fd9).

### System Info
  * Ubuntu 16.04 - 64bit
  * Processor : Intel Core i7 CPU @ 2.8GHz * 8
  * Memory : 15.5 GB
  * Disk: 44 GB
  * [ROS Kinetic](http://wiki.ros.org/kinetic/Installation/Ubuntu) if you have Ubuntu 16.04.

## Design and Strategy

### Waypoint Updater Node 
  * Handling Velocities
  * Publishing waypoints ahead
 
### Twist Controller Node
  * Handling lights
  * How I tested my stop/move algorithm


### Traffic Light Detector Node
  * changes (Topics)
  * Dataset
  * SSD
  * Lenet 5
  * Some Images
  * Rosbag Testing
  ```
  some of the printed logs from rosbag testing:
  ...
  [INFO] [1513556638.282130]: class UNKNOWN
  [INFO] [1513556638.438032]: class UNKNOWN
  [INFO] [1513556638.602744]: class RED
  [INFO] [1513556638.769951]: class RED
  [INFO] [1513556638.933516]: class RED
  [INFO] [1513556639.100313]: class RED
  ....
  [INFO] [1513560627.324544]: class YELLOW
  [INFO] [1513560627.491169]: class YELLOW
  [INFO] [1513560627.657733]: class YELLOW
  [INFO] [1513560627.825298]: class YELLOW
  ...
  [INFO] [1513556648.768566]: class GREEN
  [INFO] [1513556648.933310]: class GREEN
  [INFO] [1513556649.097478]: class GREEN
  [INFO] [1513556649.261926]: class GREEN
  [INFO] [1513556649.426090]: class GREEN


  

  

  
  ```



## Notes
 * Obstacles
 * Poor Camera Performance:
 * rivz Errors


### Real world testing Result
1. Download [training bag](https://drive.google.com/file/d/0B2_h37bMVw3iYkdJTlRSUlJIamM/view?usp=sharing) that was recorded on the Udacity self-driving car (a bag demonstraing the correct predictions in autonomous mode can be found [here](https://drive.google.com/open?id=0B2_h37bMVw3iT0ZEdlF4N01QbHc))
2. Unzip the file
```bash
unzip traffic_light_bag_files.zip
```
3. Play the bag file
```bash
rosbag play -l traffic_light_bag_files/loop_with_traffic_light.bag
```
4. Launch your project in site mode
```bash
cd CarND-Capstone/ros
roslaunch launch/site.launch
```
5. Confirm that traffic light detection works on real life images
