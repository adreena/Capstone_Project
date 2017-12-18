#!/usr/bin/env python

import rospy
from geometry_msgs.msg import PoseStamped
from styx_msgs.msg import Lane, Waypoint
from std_msgs.msg import Int32
import math

'''
This node will publish waypoints from the car's current position to some `x` distance ahead.

As mentioned in the doc, you should ideally first implement a version which does not care
about traffic lights or obstacles.

Once you have created dbw_node, you will update this node to use the status of traffic lights too.

Please note that our simulator also provides the exact location of traffic lights and their
current status in `/vehicle/traffic_lights` message. You can use this message to build this node
as well as to verify your TL classifier.

TODO (for Yousuf and Aaron): Stopline location for each traffic light.
'''

LOOKAHEAD_WPS = 200 # Number of waypoints we will publish. You can change this number


class WaypointUpdater(object):
    def __init__(self):
        self.red_light_active = False
        rospy.init_node('waypoint_updater')

        rospy.Subscriber('/current_pose', PoseStamped, self.pose_cb)
        rospy.Subscriber('/base_waypoints', Lane, self.waypoints_cb)
        
        
        self.max_velocity = self.kmph2mps(rospy.get_param('/waypoint_loader/velocity'))

        # TODO: Add a subscriber for /traffic_waypoint and /obstacle_waypoint below
        rospy.Subscriber('/traffic_waypoint',Int32, self.traffic_cb)
        rospy.Subscriber('/traffic_light_state',Int32, self.traffic_state_cb)

        self.final_waypoints_pub = rospy.Publisher('final_waypoints', Lane, queue_size=1)

        # TODO: Add other member variables you need below
        self.current_pose=None
        self.waypoints =[]
        rospy.spin()

    def pose_cb(self, msg):
        # TODO: Implement
        waypoints_ahead = Lane()
    	waypoints_ahead.header = msg.header
        waypoints_ahead.waypoints = []
        self.current_pose = msg.pose
        self.light_pose = None
    	if len(self.waypoints) > 0:
            i = 0 
    	    for waypoint in self.waypoints:
                if waypoint.pose.pose.position.x > msg.pose.position.x and len(waypoints_ahead.waypoints)< LOOKAHEAD_WPS:
                    waypoints_ahead.waypoints.append(waypoint)
                    if self.red_light_active is True:
                        if self.light_pose != None:
                            dist_to_light = waypoint.pose.pose.position.x - self.light_pose.pose.pose.position.x 
                            if dist_to_light < 5:
                                self.set_waypoint_velocity(waypoints_ahead.waypoints, i, 0)
                            elif dist_to_light <10:
                                self.set_waypoint_velocity(waypoints_ahead.waypoints, i, 5)
                            else:
                                self.set_waypoint_velocity(waypoints_ahead.waypoints, i, self.max_velocity)
                    else:
                        self.set_waypoint_velocity(waypoints_ahead.waypoints, i, self.max_velocity)
                    i+=1

        self.final_waypoints_pub.publish(waypoints_ahead)
        pass

    def waypoints_cb(self, waypoints):
        # TODO: Implement
        self.waypoints = waypoints.waypoints
        pass

    def traffic_cb(self, msg):
        # TODO: Callback for /traffic_waypoint message. Implement\
        if msg.data != -1:
            self.light_pose = self.waypoints[msg.data]
        # else: 
        #     self.red_light_active = False
           # closest_waypoint_ahead  = self.get_closest_waypoint_ahead(self.current_pose)
        pass

    def traffic_state_cb(self, msg):
        if msg.data == 0:
            self.red_light_active = True
        else: 
            self.red_light_active = False
        pass

    def obstacle_cb(self, msg):
        # TODO: Callback for /obstacle_waypoint message. We will implement it later
        pass

    def kmph2mps(self, velocity_kmph):
        return (velocity_kmph * 1000.) / (60. * 60.)

    def get_closest_waypoint_ahead(self, pose):
        """Identifies the closest path waypoint to the given position
            https://en.wikipedia.org/wiki/Closest_pair_of_points_problem
        Args:
            pose (Pose): position to match a waypoint to

        Returns:
            int: index of the closest waypoint in self.waypoints

        """
        #TODO implemented***
        min_index = 0
        if len(self.waypoints) >0:
            min_distance = float('inf')
            iterator = 0
            for waypoint in self.waypoints:
                waypoint_position = waypoint.pose.pose.position
                target_postion = pose.position
                distance = math.sqrt((waypoint_position.x - target_postion.x)**2 +\
                                     (waypoint_position.y - target_postion.y)**2  +\
                                     (waypoint_position.z - target_postion.z)**2)
                if distance < min_distance: # and waypoint_position.x > target_postion.x:
                    min_distance = distance
                    min_index = iterator
                iterator+=1
        return min_index

    def get_waypoint_velocity(self, waypoint):
        return waypoint.twist.twist.linear.x

    def set_waypoint_velocity(self, waypoints, waypoint, velocity):
        waypoints[waypoint].twist.twist.linear.x = velocity

    def distance(self, waypoints, wp1, wp2):
        dist = 0
        dl = lambda a, b: math.sqrt((a.x-b.x)**2 + (a.y-b.y)**2  + (a.z-b.z)**2)
        for i in range(wp1, wp2+1):
            dist += dl(waypoints[wp1].pose.pose.position, waypoints[i].pose.pose.position)
            wp1 = i
        return dist


if __name__ == '__main__':
    try:
        WaypointUpdater()
    except rospy.ROSInterruptException:
        rospy.logerr('Could not start waypoint updater node.')
