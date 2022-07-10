#!/usr/bin/env python
import rospy
import numpy as np
from math import sin, cos, pi
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Vector3
import flappy_config as conf


# Publisher for sending acceleration commands to flappy bird
pub_acc_cmd = rospy.Publisher('/flappy_acc', Vector3, queue_size=1)


def wall_to_far(ranges):
	no_inf_ranges = (ranges > 3.5).sum()
	to_far = True if no_inf_ranges > conf.wall_no_inf_ranges_thresh else False
	return to_far


def cap_values(val, cap):
	if val > cap[1]: return cap[1]
	elif val < cap[0]: return cap[0]
	else: return val


class Node:
	def __init__(self):
		self.initiated = False

		self.x = 0
		self.v_x = 0
		self.y = 0
		self.v_y = 0

		self.v_x_ref = conf.v_x_max
		self.y_ref = 1
		self.e_y = 0
		self.e_vy = 0
		self.wiggle = True

		self.points = []
		self.ticks = 0

		self.state = 0
		self.last_state_change = 0
		self.curr_wall = 0
		self.wall_pos = []
		self.hole_pos = 2

		## stats
		self.stat_pos = []
		self.stat_soll_pos = []

		# Here we initialize our node running the automation code
		rospy.init_node('flappy_automation_code', anonymous=True)

		# Subscribe to topics for velocity and laser scan from Flappy Bird game
		rospy.Subscriber("/flappy_vel", Vector3, self.vel_callback)
		rospy.Subscriber("/flappy_laser_scan", LaserScan, self.laser_scan_callback)


		# Ros spin to prevent program from exiting
		rospy.spin()


	def vel_callback(self, msg):
		self.x += msg.x/30
		self.y += msg.y/30
		self.v_x = msg.x/30
		self.v_y = msg.y/30
		self.stat_pos.append([self.x, self.y])
		self.stat_soll_pos.append([self.x, self.y_ref])


	def laser_scan_callback(self, msg):
		ranges = np.array(msg.ranges)
		alpha = msg.angle_increment

		if not self.initiated:
			self.initiate(ranges, alpha) #evaluate y-abs
			print("initialised ver: 0.2")

		# Perception and Mapping
		self.extend_point_list(ranges, alpha)
		self.update_wall_list(ranges, alpha)
		self.hole_pos = self.find_holes()

		# State Handling
		self.update_current_wall()
		if self.curr_wall != -1: self.state_1()

		# Acting
		self.v_controller()

		self.ticks += 1
		if self.ticks % 30 == 0:
			self.print_info()
			self.write_files()


	def state_1(self): #Vollgas
		self.v_x_ref = conf.v_x_max
		self.y_ref = self.hole_pos
		self.wiggle = False


	def extend_point_list(self, ranges, alpha):
		for (i, range) in enumerate(ranges, 1):
			if range < 3.5:	
				self.points.append(self.get_abs_pos(range, i, alpha))
		if len(self.points) > conf.point_list_length:
			self.points = self.points[- conf.point_list_length:]


	def update_wall_list(self, ranges, alpha):
		x = []
		for (i, range) in enumerate(ranges[1:8]):
			pos_x = self.get_abs_pos(range, i, alpha)[0]
			if range < 3.3:
				x.append(pos_x)
			if len(x) >= conf.wall_min_detections_thresh:
				var, mean = np.var(x), np.mean(x)
				if var < conf.wall_var_thresh:
					if len(self.wall_pos) == 0 or (mean - self.wall_pos[-1] > conf.wall_min_dist_next_wall):
						self.wall_pos.append(mean)


	def update_current_wall(self):
		body_size = conf.body_size_slow if self.v_x < 0.08 else conf.body_size_fast
		wall_ahead = np.array(self.wall_pos) + body_size > self.x 
		if np.any(wall_ahead): self.curr_wall = np.where(wall_ahead == True)[0][0] #wall is the first one ahead
		else: self.curr_wall = len(wall_ahead) - 1


	def find_holes(self):
		ps = np.array(self.points)
		if len(self.wall_pos) > 0:

			# filter points in realistic x range and y range
			x_min = self.wall_pos[self.curr_wall] + conf.hole_x_rel_range[0]
			x_max = self.wall_pos[self.curr_wall] + conf.hole_x_rel_range[1]
			ps_cut_x = ps[np.where((ps[:,0] > x_min) & (ps[:,0] < x_max))]

			ps_cut = ps_cut_x[np.where((ps_cut_x[:,1] > conf.hole_y_range[0]) & (ps_cut_x[:,1] < conf.hole_y_range[1]))]

			if len(ps_cut) > conf.min_detection_points:
				# update wall_pos
				curr_wall_pos = np.mean(np.sort(ps_cut[:,0])[:10])
				i_curr_wall = np.argmin(np.abs(self.wall_pos - curr_wall_pos))
				self.wall_pos[i_curr_wall] = curr_wall_pos

				# sort points by y
				points_y_sorted = np.sort(ps_cut[:,1])

				# measure gap size
				gap_sizes = np.diff(points_y_sorted)

				# list gaps bigger than threshold (usually 0.4)
				i_pot_gaps = np.where(gap_sizes > conf.min_gap_size)[0]

				if len(i_pot_gaps) > 0:
					# get own y-distance to gap
					distances_to_gap = [abs(points_y_sorted[i] + gap_sizes[i]/2 - self.y) for i in i_pot_gaps]

					# chose gap that is the closest to you
					i_best_gap = i_pot_gaps[np.argmin(distances_to_gap)]

					gap_pos = points_y_sorted[i_best_gap] + gap_sizes[i_best_gap]/2
					return gap_pos

		return self.y #stay where you are if there is not enough information
	

	def get_new_points(self, ranges, alpha):
		new_points = []
		for (i, range) in enumerate(ranges, 1):
			if range < 3.5:	
				new_points.append(self.get_abs_pos(range, i, alpha))
		return new_points


	def get_abs_pos(self, range, i, alpha):
		angle = (-5+i)*alpha
		x = self.x + range * cos(angle)
		y = self.y + range * sin(angle)

		return [x,y]


	def v_controller(self):
		# y Wiggleing
		if self.wiggle: #wiggling
			if self.ticks / conf.wiggle["ticks"] % 2 == 0:
				self.y_ref = conf.wiggle["y_min"]
			else: self.y_ref = conf.wiggle["y_max"]
		self.y_ref = cap_values(self.y_ref, conf.cap_y)

		# y Velocity Controller
		diff_y = (self.y_ref - self.y) - self.e_y
		self.e_y = self.y_ref - self.y
		v_y_contr = conf.vel_contr["kp"] * self.e_y + conf.vel_contr["kd"] * diff_y

		# y Acceleration Controller
		diff_vy = (v_y_contr - self.v_y) - self.e_vy
		self.e_vy = v_y_contr - self.v_y
		a_y_contr = conf.acc_contr["kp"] * self.e_vy + conf.acc_contr["kd"] * diff_vy

		# x Acceleration Controller
		a_x_contr = np.sign(self.v_x_ref - self.v_x) * 30

		# Emergency Brake
		if self.curr_wall > -1:
			dist_to_wall = self.wall_pos[self.curr_wall] - self.x
			if conf.em_brake["max"] > dist_to_wall > conf.em_brake["min"] and abs(self.e_y) > conf.em_brake["e_y"]:
				a_x_contr = -1000000

		# Publish
		pub_acc_cmd.publish(Vector3(a_x_contr, a_y_contr, 0))


	def initiate(self, ranges, angle):
		self.y = sin(angle*4)*ranges[0]
		self.initiated = True
	

	def print_info(self):
		print("pos: ({},{}), vel: ({},{})".format(round(self.x, 3), round(self.y,3), round(self.v_x, 3), round(self.v_y,3)))
		print("ticks: {}, wall number: {}".format(self.ticks, self.curr_wall))


	def my_print(self, text, n_ticks=10):
		if self.ticks % n_ticks == 0:
			print(text)


	def write_files(self):
		if conf.write_files:
			filenames = ["points.txt", "pos.txt", "walls.txt", "soll_pos.txt"]
			texts = [str(self.points), str(self.stat_pos), str(self.wall_pos), str(self.stat_soll_pos)]
			for (filename, text) in zip(filenames, texts):
				file = open(conf.f_dir + filename, "w")
				file.write(text)
				file.close


if __name__ == '__main__':
    try:
        myNode = Node()
    except rospy.ROSInterruptException:
        pass
