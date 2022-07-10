## CONFIG
v_x_max = 0.075
body_size_fast = 0.35
body_size_slow = 0.35

# first wall detection
wall_no_inf_ranges_thresh = 4

# wall detection
wall_min_detections_thresh = 4
wall_var_thresh = 0.3
wall_min_dist_next_wall = 1

# hole detection
hole_y_range = [0.4, 3.6]
hole_x_rel_range = [-0.6, 1.3]
min_detection_points = 30
min_gap_size = 0.4

# Controller
# x
em_brake = {"min": 0, "max": 0.7, "e_y": 1}

# y
vel_contr = {"kp": 0.23, "kd": 0.1}
acc_contr = {"kp": 630, "kd": 120}
cap_y = [0.75, 3.25]
wiggle = {"y_min": 1.8, "y_max": 1.8, "ticks": 10}


# Data saver
point_list_length = 500
write_files = False
f_dir = "/home/flyatest/Desktop/"
