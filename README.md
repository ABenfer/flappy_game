# Flappy Game

[Original link](https://github.com/JohsBL/flappy_automation_test)




This is just a brief summary of the most interesting parts of the code. If you have any further questions, feel free to email me at <achim.benfer@outlook.de>.

To run the code make sure the python file has the permission to be executed. There are two config files: The first one (“flappy_config.py”) is a save version that does around 60 points with a very high chance of succeeding. The second one (“flappy_config_fast.py”) is more aggressive and aims for a score of 100+. However it fails in about 60% of tries. To try the fast config, just rename the config file to “flappy_config.py”.

## Code Breakdown

I structured the task in the subtasks perception and mapping, state handling and acting. In the beginning I used the three different states, exploring, positioning and full throttle to manage the task. Over time the subsystems got better, which allowed me to combined all the states to a continuous perception, mapping and acting state. 

### Perception and Mapping
To accomplish the mapping task I had multiple concepts. One was to create an occupancy grid and then aim for the one that was occupied the least. The concept worked but had some problems for example if one wall occupied two rows in x-direction. In the end I used a point cloud and searched for gaps of a minimum size in y-direction. Because the gaps are only in a certain y-range I capped the area of interest. If it detects more than one gap, it takes the one closest to its current y-position, which works better than looking for the biggest gap. It then outputs the center of the gap. 

The walls are detected in a two-step process. The first step is inaccurate but detects the front of the wall before it enters the one before. In the following steps it then increases the accuracy of the approximation. The exact position of the wall is crucial as it is important to adjust the y-position for the next wall as soon as possible. If it adjusts the position to early it hits the current wall.

### Acting
To control the bird I used a P-controller for the x-speed. It doesn’t make a big difference if you use variable speeds in x-direction, so I just used a static velocity. In case the bird is completely off, it activates an emergency brake, that does maximum deceleration. However the effect of it is very little.

In y-direction I wanted to define the position instead of the speed. As a consequence I built a 2 stage cascaded PD-controller. The first stage controls the position and the second one the y-speed. The integral element is not needed, because there is no noice and therefore no stationary inaccuracy. 

### Visualisation
To analyse errors in the code and to tune the model I created visualisations. As you can see the main limitation of the automation and the reason I think I am approaching a limit is the acceleration in y-direction, which is capped by the game.

![Map](https://paper-attachments.dropbox.com/s_BAA2E558C14F7C8036E2E8CF3D61765F9827C058A70CE5AD1203D4919BF35D00_1657367975842_test-10.png)


In the images below you can see an error that occurred because it wrongly detected a gap. In order to erase this error, the minimum amount of points needed to detect a gap has to be increased.

![Incorrect gap detection](https://paper-attachments.dropbox.com/s_BAA2E558C14F7C8036E2E8CF3D61765F9827C058A70CE5AD1203D4919BF35D00_1657368068365_test-13.png)


In this picture you can see the opposite error. It took too long to detect a valid gap, so it the controller was too late. 

![Late gap detection](https://paper-attachments.dropbox.com/s_BAA2E558C14F7C8036E2E8CF3D61765F9827C058A70CE5AD1203D4919BF35D00_1657368197493_test-14.png)


If you want to create the illustrations on your own, change “write_files” in the config file to True and increase “point_list_length” to 100.000 (it caps the point list to a size of 500 to reduce computing time). Then run “illustrate.py” with the files in the directory specified in the config file as “f_dir”.

As a conclusion I think I got close to the optimum solution. There could be some potential in having a dynamic x-speed depending on the y-distance to the gap. However as the maximum acceleration in x-direction is very small, the potential is limited. Also tuning the controller further could result in less overshoot crashes or faster reaction time.
