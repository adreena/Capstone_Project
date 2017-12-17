import rospy
from yaw_controller import YawController
from pid import PID

GAS_DENSITY = 2.858
ONE_MPH = 0.44704 # mph to mps
SAMPLE_TIME_MIN = 0.02


class Controller(object):
    def __init__(self, *args, **kwargs):
        # TODO: Implement
        self.wheel_base = None
        self.steer_ratio = None
        self.min_speed = None
        self.max_lat_accel = None
        self.max_steer_angle = None
        self.accel_limit = None
        self.decel_limit = None
        self.brake_active = False
        self.prev_time = None

        self._test_timer = None
        self._test_light_state= 0

        for key in kwargs:
            if key == "wheel_base":
        	    self.wheel_base = kwargs[key]
            elif key == "steer_ratio":
            	self.steer_ratio = kwargs[key]
            elif key == "min_speed":
        	    self.min_speed = kwargs[key]
            elif key == "max_lat_accel":
        	    self.max_lat_accel = kwargs[key]
            elif key == "max_steer_angle":
        	    self.max_steer_angle = kwargs[key]
            elif key == "accel_limit":
                self.accel_limit = kwargs[key]
            elif key == "decel_limit":
                self.decel_limit = kwargs[key]
            elif key == "fuel_capacity":
                self.fuel_capacity = kwargs[key]
            elif key == "wheel_radius":
                self.wheel_radius = kwargs[key]
            elif key == "vehicle_mass":
                self.vehicle_mass = kwargs[key]
            elif key == "max_velocity": 
                self.max_velocity = kwargs[key]
            

        self.yaw_controller = YawController(self.wheel_base, self.steer_ratio,\
                              self.min_speed, self.max_lat_accel, self.max_steer_angle)
        self.pid_throttle = PID(kp=8., ki=0.0, kd=0.5)

        self.debug_counter =0
        pass

    def apply_brake(self):
        acceleration = self.accel_limit
        return (self.vehicle_mass + self.fuel_capacity * GAS_DENSITY )* acceleration * self.wheel_radius

    def control(self, *args, **kwargs):

        full_brake = self.apply_brake()
        
        if not kwargs["dbw_enabled"] or self.prev_time is None : 
            self.prev_time = rospy.Time.now().to_sec()

            return 0.0, 0.0, 0.0, 0.0, 0.0

        brake = 0
        current_time = rospy.Time.now().to_sec()

        # TODO: Change the arg, kwarg list to suit your needs
        current_velocity_linear = kwargs["current_velocity_linear"]
        target_velocity_linear = kwargs["target_velocity_linear"]
        target_velocity_angular = kwargs["target_velocity_angular"]
        distance_to_light= kwargs["distance_to_light"]
        light_state= kwargs["light_state"]
        # create pid for throttle sample_time, cte
        sample_time = max(current_time - self.prev_time, SAMPLE_TIME_MIN)
        
        # ENDING points ahead should brake and stop the car

        # possible scenarios 
        # case red light then green in 10 sec
        # target_velocity_linear.x = 10

        # if self._test_timer is None:
        #     self._test_timer = current_time + 10.0
        #     self._test_light_state  =0
        
        # distance_to_light = 50
        # light_state = self._test_light_state 

        # if current_time > self._test_timer :
        #     if self._test_light_state == 0:
        #         self._test_light_state = 2
        #     elif self._test_light_state == 2:
        #         self._test_light_state = 1
        #     elif self._test_light_state == 1:
        #         self._test_light_state = 0

        #     light_state = self._test_light_state
        #     self._test_timer = current_time + 10.0



        if kwargs["number_waypoints_ahead"] < 150:
            rospy.loginfo('applying 1')
            if kwargs["number_waypoints_ahead"] < 25:
                brake = full_brake # ~360
            elif kwargs["number_waypoints_ahead"] < 50:
                brake = full_brake * 0.5 
            elif kwargs["number_waypoints_ahead"] < 75:
                brake = full_brake * 0.1 
            elif kwargs["number_waypoints_ahead"] < 125:
                brake = full_brake * 0.05 
            else:
                brake = full_brake * 0.01 # ~3.6
            
            throttle = 0.0
            steer = self.yaw_controller.get_steering(0, 0, current_velocity_linear.x)
            return throttle, brake, steer, current_time, self._test_light_state

        else:
            
            max_speed_mps = self.max_velocity*ONE_MPH
            target_velocity = min(max_speed_mps, target_velocity_linear.x)
            v_error = target_velocity - current_velocity_linear.x
            if light_state == 0:
                if distance_to_light < 15:
                    brake = full_brake
                elif distance_to_light < 25:
                    brake = 20
                else:
                    brake = 10

                self.pid_throttle.reset()
                return 0.,brake,0., current_time,self._test_light_state 
            elif light_state == 1:
                brake = 10.
                return 0.,brake,0., current_time,self._test_light_state 
            else:
                brake = 0.
                v_decel = self.decel_limit*sample_time
                v_accel = self.accel_limit*sample_time
                v_error = min(v_error, v_accel)
                v_error = max(v_error, v_decel)

                throttle = self.pid_throttle.step(error= v_error, sample_time=sample_time)
                throttle = max(throttle, 0.)

                # call yaw controller  linear_velocity, angular_velocity, current_velocity
                steer = self.yaw_controller.get_steering(target_velocity_linear.x, target_velocity_angular.z,\
                			    current_velocity_linear.x)
                self.prev_time = current_time
                # Return throttle, brake, steer
                return throttle, brake, steer, current_time, self._test_light_state
