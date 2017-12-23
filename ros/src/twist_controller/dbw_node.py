#!/usr/bin/env python

import rospy
from std_msgs.msg import Bool
from styx_msgs.msg import Lane
from dbw_mkz_msgs.msg import ThrottleCmd, SteeringCmd, BrakeCmd, SteeringReport
from geometry_msgs.msg import TwistStamped , PoseStamped
from std_msgs.msg import Int32
import math

from twist_controller import Controller

'''
You can build this node only after you have built (or partially built) the `waypoint_updater` node.

You will subscribe to `/twist_cmd` message which provides the proposed linear and angular velocities.
You can subscribe to any other message that you find important or refer to the document for list
of messages subscribed to by the reference implementation of this node.

One thing to keep in mind while building this node and the `twist_controller` class is the status
of `dbw_enabled`. While in the simulator, its enabled all the time, in the real car, that will
not be the case. This may cause your PID controller to accumulate error because the car could
temporarily be driven by a human instead of your controller.

We have provided two launch files with this node. Vehicle specific values (like vehicle_mass,
wheel_base) etc should not be altered in these files.

We have also provided some reference implementations for PID controller and other utility classes.
You are free to use them or build your own.

Once you have the proposed throttle, brake, and steer values, publish it on the various publishers
that we have created in the `__init__` function.

'''

class DBWNode(object):
    def __init__(self):
        rospy.init_node('dbw_node', log_level=rospy.DEBUG)

        self.light_state  = None
        self.distance_to_light = None
        self.brake_active_count=0
        self.brake_active = False
        self.dbw_enabled_count = 0

        vehicle_mass = rospy.get_param('~vehicle_mass', 1736.35)
        fuel_capacity = rospy.get_param('~fuel_capacity', 13.5)
        brake_deadband = rospy.get_param('~brake_deadband', .1)
        decel_limit = rospy.get_param('~decel_limit', -5)
        accel_limit = rospy.get_param('~accel_limit', 1.)
        wheel_radius = rospy.get_param('~wheel_radius', 0.2413)
        wheel_base = rospy.get_param('~wheel_base', 2.8498)
        steer_ratio = rospy.get_param('~steer_ratio', 14.8)
        max_lat_accel = rospy.get_param('~max_lat_accel', 3.)
        max_steer_angle = rospy.get_param('~max_steer_angle', 8.)

        self.steer_pub = rospy.Publisher('/vehicle/steering_cmd',
                                         SteeringCmd, queue_size=1)
        self.throttle_pub = rospy.Publisher('/vehicle/throttle_cmd',
                                            ThrottleCmd, queue_size=1)
        self.brake_pub = rospy.Publisher('/vehicle/brake_cmd',
                                         BrakeCmd, queue_size=1)

        self.max_velocity = self.kmph2mps(rospy.get_param('/waypoint_loader/velocity'))

        # TODO: Create `TwistController` object
        self.controller = Controller(wheel_base=wheel_base, steer_ratio= steer_ratio,\
				     decel_limit=decel_limit, accel_limit= accel_limit,\
                     min_speed=0.0, max_lat_accel=max_lat_accel, max_steer_angle=max_steer_angle,\
				     fuel_capacity=fuel_capacity, wheel_radius=wheel_radius,\
				     vehicle_mass = vehicle_mass, max_velocity=self.max_velocity)

        # TODO: Subscribe to all the topics you need to

    	self.current_velocity = TwistStamped()
    	rospy.Subscriber('/current_velocity',TwistStamped,self.current_velocity_cb)

    	self.target_velocity = TwistStamped()
    	rospy.Subscriber('/twist_cmd', TwistStamped, self.twist_cmd_cb)

    	self.dbw_enabled = False
        rospy.Subscriber('/vehicle/dbw_enabled',Bool, self.dbw_enabled_cb)

        self.number_waypoints_ahead=None
        self.waypoints = []
        rospy.Subscriber('/final_waypoints', Lane, self.final_waypoints_cb)
        rospy.Subscriber('/base_waypoints', Lane, self.waypoints_cb)

        rospy.Subscriber('/traffic_light_state', Int32, self.upcoming_traffice_light_state_cb)
        rospy.Subscriber('/traffic_waypoint',Int32, self.upcoming_traffice_wp_cb)

        self.current_pose=None
        rospy.Subscriber('/current_pose', PoseStamped, self.pose_cb)

        self.loop()

    def kmph2mps(self, velocity_kmph):
        return (velocity_kmph * 1000.) / (60. * 60.)

    def pose_cb(self, msg):
        # TODO: Implement
        self.current_pose = msg
        pass

    def waypoints_cb(self, waypoints):
        # TODO: Implement
        self.waypoints = waypoints.waypoints
        pass

    def current_velocity_cb(self, data):
        self.current_velocity = data
        pass

    def final_waypoints_cb(self,data):
        self.number_waypoints_ahead=len(data.waypoints)
        pass

    def upcoming_traffice_wp_cb(self, msg):
        if msg.data != -1:
            traffic_wp = self.waypoints[msg.data]
            self.distance_to_light = traffic_wp.pose.pose.position.x - self.current_pose.pose.position.x
        pass

    def upcoming_traffice_light_state_cb(self, msg):
        self.light_state = msg.data
        pass

    def twist_cmd_cb(self,data):
        #recieved target velocity
        self.target_velocity = data
        pass

    def dbw_enabled_cb(self, data):
        self.dbw_enabled = data.data
        self.dbw_enabled_count =0
        rospy.loginfo('CALL dbw_enabled:{}, {}'.format(self.dbw_enabled, type(self.dbw_enabled)))
        pass

    def loop(self):
        rate = rospy.Rate(50) # 50Hz
        while not rospy.is_shutdown():
            # TODO: Get predicted throttle, brake, and steering using `twist_controller`
            # You should only publish the control commands if dbw is enabled
            
            if self.dbw_enabled is True:
                throttle, brake, steer, _time, _state = self.controller.control(current_velocity_linear= self.current_velocity.twist.linear,\
                target_velocity_angular=self.target_velocity.twist.angular,\
                target_velocity_linear= self.target_velocity.twist.linear,\
                dbw_enabled=self.dbw_enabled, number_waypoints_ahead=self.number_waypoints_ahead,\
                distance_to_light= self.distance_to_light, light_state= self.light_state )
                rospy.loginfo('AUTO dbw_enabled:{}'.format(self.dbw_enabled))

                self.publish(throttle, brake, steer, _time, _state)
            else:
                if self.dbw_enabled_count == 0:
                    self.dbw_enabled_count =1 
                    self.controller.pid_throttle.reset()
                    self.publish(0., 0., 0.)
                else:
                    pass
                rospy.loginfo('DBW dbw_enabled: {}'.format(self.dbw_enabled))
            rate.sleep()

    def publish(self, throttle, brake, steer,_time=0, _state=0):
        try:
            tcmd = ThrottleCmd()
            tcmd.enable = True
            tcmd.pedal_cmd_type = ThrottleCmd.CMD_PERCENT
            tcmd.pedal_cmd = throttle
            self.throttle_pub.publish(tcmd)

            scmd = SteeringCmd()
            scmd.enable = True
            scmd.steering_wheel_angle_cmd = steer
            self.steer_pub.publish(scmd)
        
            bcmd = BrakeCmd()
            bcmd.enable = True
            bcmd.pedal_cmd_type = BrakeCmd.CMD_TORQUE
            bcmd.pedal_cmd = brake
            self.brake_pub.publish(bcmd)
            rospy.loginfo('{} : PUBLISH_throttle:{} , brake:{} , steer:{}, light:{}'.format(_time, throttle, brake, steer, _state))
        except Exception as err:
            rospy.loginfo('v_error: ERROR {} '.format(err))


if __name__ == '__main__':
    try:
        DBWNode()
    except rospy.ROSInterruptException:
        rospy.logerr('Could not start dbw node.')

