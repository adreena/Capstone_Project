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
                # kmh to mph
                self.max_velocity = kwargs[key] * 0.621371

        self.yaw_controller = YawController(self.wheel_base, self.steer_ratio,\
        self.min_speed, self.max_lat_accel, self.max_steer_angle)
        self.pid_throttle = PID(kp=2.0, ki=0.00001, kd=8.0)

        self.debug_counter =0
        pass

    def apply_brake(self, acceleration):
        self.brake_active= True
        return (self.vehicle_mass + self.fuel_capacity * GAS_DENSITY )* acceleration * self.wheel_radius

    def control(self, *args, **kwargs):
        # TODO: Change the arg, kwarg list to suit your needs
        # Return throttle, brake, steer
        if not kwargs["dbw_enabled"] or self.prev_time is None:
            self.prev_time = rospy.Time.now().to_sec()
            return 0.0, 0.0, 0.0

        brake = 0
        if kwargs["number_waypoints_ahead"] <= 50: # or self.debug_counter > 1000:
            # no points ahead should brake and stop the car
            brake = self.apply_brake(self.accel_limit)

        current_time = rospy.Time.now().to_sec()

        # TODO: Change the arg, kwarg list to suit your needs
        current_velocity_linear = kwargs["current_velocity_linear"]
        target_velocity_linear = kwargs["target_velocity_linear"]
        target_velocity_angular = kwargs["target_velocity_angular"]

        # create pid for throttle sample_time, cte
        sample_time = current_time - self.prev_time

        if self.brake_active:
            throttle = 0.0
            target_velocity_linear.x = 0.0
        else:
            max_speed_mps = self.max_velocity*ONE_MPH
            target_velocity = min(max_speed_mps, target_velocity_linear.x)
            v_error = target_velocity - current_velocity_linear.x
            v_decel = self.decel_limit*sample_time
            v_accel = self.accel_limit*sample_time
            v_error = min(v_error, v_accel)
            v_error = max(v_error, v_decel)
            throttle = self.pid_throttle.step(error= v_error, sample_time=sample_time)
            throttle = min(max(0.0 , throttle), max_speed_mps)

        # call yaw controller  linear_velocity, angular_velocity, current_velocity
        steer = self.yaw_controller.get_steering(target_velocity_linear.x, target_velocity_angular.z,\
        			    current_velocity_linear.x)
        self.prev_time = current_time
        self.brake_active = False
        self.debug_counter +=1
        # Return throttle, brake, steer
        return throttle, brake, steer
