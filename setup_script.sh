sudo sh -c 'echo "deb [ arch=amd64 ] http://packages.dataspeedinc.com/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-dataspeed-public.list'
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys FF6D3CDA
sudo apt-get update

# setup rosdep
sudo sh -c 'echo "yaml http://packages.dataspeedinc.com/ros/ros-public-'$ROS_DISTRO'.yaml '$ROS_DISTRO'" > /etc/ros/rosdep/sources.list.d/30-dataspeed-public-'$ROS_DISTRO'.list'
sudo rosdep update
sudo apt-get install -y ros-$ROS_DISTRO-dbw-mkz
sudo apt-get upgrade -y
# end installing Dataspeed DBW

# install python packages
sudo apt-get install -y python-pip
pip install -r requirements.txt

# install required ros dependencies
sudo apt-get install -y ros-$ROS_DISTRO-cv-bridge
sudo apt-get install -y ros-$ROS_DISTRO-pcl-ros
sudo apt-get install -y ros-$ROS_DISTRO-image-proc

# socket io
sudo apt-get install -y netbase
