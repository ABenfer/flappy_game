import numpy as np
from matplotlib import pyplot as plt

with open('points.txt', 'r') as f:
	points = f.read()
with open('pos.txt', 'r') as f:
	pos = f.read()
with open('soll_pos.txt', 'r') as f:
	soll_pos = f.read()
with open('walls.txt', 'r') as f:
	walls = f.read().replace('[', '').replace(']', '').split(',')

# point cloud
points = points.replace('[', '').replace(']', '')
x = points.split(', ')[::2]
y = points.split(', ')[1::2]
x = [float(el) for el in x]
y = [float(el) for el in y]

# bird position
pos = pos.replace('[', '').replace(']', '')
pos_x = pos.split(', ')[::2]
pos_y = pos.split(', ')[1::2]
pos_x = [float(el) for el in pos_x]
pos_y = [float(el) for el in pos_y]

# reference position
soll_pos = soll_pos.replace('[', '').replace(']', '')
soll_pos_y = soll_pos.split(', ')[1::2]
soll_pos_y = [float(el) for el in soll_pos_y]

# walls
walls = [float(w) for w in walls]

plt.plot(pos_x, soll_pos_y[:len(pos_x)], c='green', alpha=0.5)
plt.plot(pos_x, pos_y, c='red')
plt.scatter(x,y, s=0.2)
for w in walls:
    plt.plot([w,w], [0,4], c="black", alpha=0.2)

plt.axis('equal')
plt.xlim(pos_x[-1] - 10, pos_x[-1])
plt.legend(['ref pos', 'pos', 'wall front'])

plt.show()
#plt.savefig('test.png', dpi=1000)