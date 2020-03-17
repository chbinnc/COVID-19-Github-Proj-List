import os, subprocess, inspect
from datetime import datetime, timezone
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

getdir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))  # http://stackoverflow.co>
os.chdir(getdir)

completed_process = subprocess.run("git log --stat Wuhan_nCoV_Github_Project_list.csv | grep Date:", shell=True, stdout=subprocess.PIPE)
date_list = completed_process.stdout.decode("utf-8").split('\n')
completed_process = subprocess.run("git log --stat Wuhan_nCoV_Github_Project_list.csv | grep changed", shell=True, stdout=subprocess.PIPE)
line_changed_list = completed_process.stdout.decode("utf-8").split('\n')

new_modified_list = []
total_line_count = 0
for line in line_changed_list[0:-1][::-1]:
    line = line.split()
    if line[-3] == 'insertions(+),':
        insertions = int(line[-4])
        deletions = int(line[-2])
        new = insertions - deletions
        modified = deletions
        total_line_count += new
        new_modified_list.append([total_line_count, new, modified])
    elif line[-1] == 'insertions(+)': # first commit, only insertion
        insertions = int(line[-2])
        total_line_count += insertions
        new_modified_list.append([total_line_count, insertions, 0])
    else: # manually deleting unrelated project, only deletion
        deletions = int(line[-2])
        total_line_count -= deletions
        new_modified_list.append([total_line_count, 0, 0])

x = [datetime.strptime(d, 'Date:   %a %b %d %H:%M:%S %Y %z') for d in date_list[0:-1][::-1]]
y0 = [i[0] for i in new_modified_list]
y1 = [i[1] for i in new_modified_list]
y2 = [i[2] for i in new_modified_list]
y2[8:10] = [y2[10], y2[10]] # same date, noise

fig, ax_list = plt.subplots(2, figsize=(10,5))

for index, ax in enumerate(ax_list):
    if index == 0:
        ax.plot(x, y0, label='total', marker='x', markersize=5)
    else:
        ax.plot(x, y1, label='new', marker='+', markersize=5)
        ax.plot(x, y2, label='modified', marker='1', markersize=5)
    ax.legend(loc='upper left')
    ax.grid()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
    plt.gcf().autofmt_xdate()
plt.savefig('trend_plot.png')