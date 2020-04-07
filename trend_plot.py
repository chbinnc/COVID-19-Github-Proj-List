import os, subprocess, inspect
from datetime import datetime, timezone
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

getdir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))  # http://stackoverflow.co>
os.chdir(getdir)

completed_process = subprocess.run("git log --stat Wuhan_nCoV_Github_Project_list.csv | \
        grep Date:", shell=True, stdout=subprocess.PIPE)
date_list = completed_process.stdout.decode("utf-8").split('\n')
completed_process = subprocess.run("git log --stat Wuhan_nCoV_Github_Project_list.csv | \
        grep changed", shell=True, stdout=subprocess.PIPE)
line_changed_list = completed_process.stdout.decode("utf-8").split('\n')
completed_process = subprocess.run("git log -p Wuhan_nCoV_Github_Project_list.csv | \
        grep ^+", shell=True, stdout=subprocess.PIPE)
project_meta_list = completed_process.stdout.decode("utf-8").split('+++')

new_modified_list = []
user_list = []
new_user_count_list = []
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

for line in project_meta_list[1:][::-1]:
    user_count = 0
    project_list = line.strip().split('\n')[1:]
    for project in project_list:
        try:
            user_name = project.split('\t')[1].split('/')[3]
            if user_name not in user_list:
                user_count += 1
                user_list.append(user_name)
        except Exception as err:
            pass
    if user_count == 0 and len(line.split('\n')) == 1:
        continue
    else:
        new_user_count_list.append(user_count)

# weird data, cause needs further investigation, temporarily regarded as noise
new_user_count_list[38] += new_user_count_list[37]
del(new_user_count_list[37])

x = [datetime.strptime(d, 'Date:   %a %b %d %H:%M:%S %Y %z') for d in date_list[0:-1][::-1]]
y0 = [i[0] for i in new_modified_list]
y1 = [i[1] for i in new_modified_list]
y2 = [i[2] for i in new_modified_list]
y3 = new_user_count_list

def mergeToNext(i):
    x[i] = x[i + 1]
    y0[i] = y0[i + 1]
    y1[i + 1] += y1[i]
    y3[i + 1] += y3[i]
    y1[i] = y1[i + 1]
    y2[i] = y2[i + 1]
    y3[i] = y3[i + 1]
# noise
mergeToNext(9) # y2[9] = 1834 = y0[8]
mergeToNext(2) # y1[2:4] = [2, 279]
mergeToNext(4) # y1[4:6] = [8, 628]
mergeToNext(47) # y1[45:50] = [733, 675, 245, 596, 728]

def removeNoise(y):
    for index, value in enumerate(y):
        if value == 0 and index != 0:
            y[index] = y[index - 1]
            x[index] = x[index - 1]
removeNoise(y1)
removeNoise(y2)
removeNoise(y3)

total_user_count_list = [y3[0]]
for i in y3[1:]:
    total_user_count_list.append(total_user_count_list[-1] + i)
y4 = total_user_count_list

fig, ax_list = plt.subplots(2, figsize=(10,5))

for index, ax in enumerate(ax_list):
    if index == 0:
        ax.plot(x, y0, label='total project', marker='x', markersize=5)
        ax.plot(x, y4, label='total user', marker='1', markersize=5)
    else:
        ax.plot(x, y1, label='new project', marker='+', markersize=5)
        ax.plot(x, y2, label='modified', marker='1', markersize=5)
        ax.plot(x, y3, label='new user', marker='2', markersize=5)
    ax.legend(loc='upper left')
    ax.grid()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
plt.gcf().autofmt_xdate()
plt.savefig('trend_plot.png')
