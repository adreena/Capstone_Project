#!/usr/bin/env python

import rospy
from std_msgs.msg import Bool
from styx_msgs.msg import Lane
from dbw_mkz_msgs.msg import ThrottleCmd, SteeringCmd, BrakeCmd, SteeringReport
from geometry_msgs.msg import TwistStamped
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

        self.max_velocity = rospy.get_param('/waypoint_loader/velocity')

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
        rospy.Subscriber('/final_waypoints', Lane, self.final_waypoints_cb)

        # rospy.Subscriber('/traffic_waypoint',Int32, self.traffic_cb)
        # rospy.loginfo('dbw Initialized')
        self.loop()

    def current_velocity_cb(self, data):
        self.current_velocity = data
        pass

    def final_waypoints_cb(self,data):
        self.number_waypoints_ahead=len(data.waypoints)
        rospy.loginfo(self.number_waypoints_ahead)
        pass

    def traffic_cb(self, msg):
        # TODO: Callback for /traffic_waypoint message. Implement\
        # if msg.data != -1:
        #     self.set_waypoint_velocity(self.waypoints, msg.data, 0.0)
        #     self.red_light_active = True
        # else: 
        #    self.red_light_active = False
        #    closest_waypoint_ahead  = self.get_closest_waypoint_ahead(self.current_pose)
        #    self.set_waypoint_velocity(self.waypoints, closest_waypoint_ahead, 10.0)
           # rospy.logdebug('red light state {} {}'.format(self.red_light_active, self.get_waypoint_velocity(self.waypoints[closest_waypoint_ahead])))
        pass

    def twist_cmd_cb(self,data):
        #recieved target velocity
        self.target_velocity = data
        # rospy.loginfo("twist_cmd_cb")
        #throttle, brake, steer, sample_time, error_v = self.controller.control(current_velocity_linear=self.target_velocity.twist.linear,\
        #                target_velocity_angular=self.target_velocity.twist.angular,\
        #                target_velocity_linear=self.current_velocity.twist.linear,\
        #                 dbw_enabled=self.dbw_enabled, number_waypoints_ahead=self.number_waypoints_ahead)
        #rospy.loginfo("published_loop {0},{1},{2}, {3}, {4}".format(throttle, brake, steer, sample_time, error_v))
        #if self.dbw_enabled:
        #    self.publish(throttle, brake, steer)
        pass

    def dbw_enabled_cb(self, data):
        # rospy.loginfo('dwb_enabled_cb:{}'.format(data.data))
        self.dbw_enabled = data.data
        pass

    def loop(self):
        rate = rospy.Rate(50) # 50Hz
        # rospy.logdebug("#ahead :{}".format(self.number_waypoints_ahead))
        while not rospy.is_shutdown():
            # TODO: Get predicted throttle, brake, and steering using `twist_controller`
            # You should only publish the control commands if dbw is enabled
            # throttle, brake, steering = self.controller.control(<proposed linear velocity>,
            #                                                     <proposed angular velocity>,
            #                                                     <current linear velocity>,
            #                                                     <dbw status>,
            #                                                     <any other argument you need>)
            # if <dbw is enabled>:
            #   self.publish(throttle, brake, steer)
            throttle, brake, steer = self.controller.control(current_velocity_linear=self.target_velocity.twist.linear,\
            	target_velocity_angular=self.target_velocity.twist.angular,\
            	target_velocity_linear=self.current_velocity.twist.linear,\
            	dbw_enabled=self.dbw_enabled, number_waypoints_ahead=self.number_waypoints_ahead)

            if self.target_velocity.twist.linear.x == 0.0:
                rospy.logdebug('Target_Velocity 0.0 throttle:{}'.format(throttle))
                # brake = self.controller.apply_brake()
            
            if brake != 0.0:
                rospy.loginfo("published_loop {0},{1},{2}".format(throttle, brake, steer))
            if self.dbw_enabled:
            	 self.publish(throttle, brake, steer)
            rate.sleep()

    def publish(self, throttle, brake, steer):
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


if __name__ == '__main__':
    try:
        DBWNode()
    except rospy.ROSInterruptException:
        rospy.logerr('Could not start dbw node.')

