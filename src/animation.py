# from collections import deque
# import matplotlib.pyplot as plt
# import matplotlib.animation as animation
# import numpy as np

# def animate(i):
#     global x
#     x += np.abs(np.random.randn())
#     y = np.random.randn()
#     data.append((x, y))
#     ax.relim()
#     ax.autoscale_view()
#     line.set_data(*zip(*data))

# fig, ax = plt.subplots()
# x = 0
# y = np.random.randn()
# data = deque([(x, y)], maxlen=10)
# line, = plt.plot(*zip(*data), c='black')

# ani = animation.FuncAnimation(fig, animate, interval=100)
# plt.show()

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style

style.use('fivethirtyeight')

fig = plt.figure()
ax1 = fig.add_subplot(1,1,1)

def animate(i):
    graph_data = open('../data.txt','r').read()
    lines = graph_data.split('\n')
    xs = []
    ys = []
    for line in lines:
        if len(line) > 1:
            x, y = line.split(',')
            textstr = 'CPU usage = %d\nNum of workers = %d'%(float(x),int(y))
            xs.append(int(x))
            ys.append(int(y))
    ax1.clear()
    ax1.relim()
    ax1.autoscale_view()
    # these are matplotlib.patch.Patch properties
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    # place a text box in upper left in axes coords
    ax1.text(0.05, 0.95, textstr, transform=ax1.transAxes, fontsize=14,
            verticalalignment='top', bbox=props)
    ax1.plot(xs, ys)


ani = animation.FuncAnimation(fig, animate, interval=1000)
plt.show()

