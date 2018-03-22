import sys
import re
import getopt
import texttable as tt
import math
from datetime import datetime

class Log():
    def __init__(self, row):
        self.row = row.strip()
        # parse raw data
        # parse time
        self.time = datetime.strptime(re.compile('.+? *\d{2} *\d{2}:\d{2}:\d{2}')
                                      .search(self.row)
                                      .group(), '%b %d %H:%M:%S').replace(year=2018)
        # parse user name
        self.user = re.compile('.*(I|i)nvalid user (.+? )').search(self.row).group(2).strip()

def draw_summary(sum):
    tab = tt.Texttable()

    # set center align.
    tab.set_cols_align(["c", "c"])

    # don't use vertical line beteew cols.
    tab.set_deco(tt.Texttable.HEADER + tt.Texttable.BORDER + tt.Texttable.VLINES)

    # set line below header as "-"
    tab.set_chars(['-', '|', '+', '-'])

    # header text
    headings = ['user', 'count']
    tab.header(headings)

    # append table row
    for row in sum:
        tab.add_row(row)

    # print out table
    print(tab.draw())

def main(
    sort_by_user = False,
    before = datetime(3000, 1, 1),
    after = datetime(1900, 1, 1),
    max = math.inf,
    min = 0,
    reverse = False):

    # parse arguments
    opts, args = getopt.getopt(sys.argv[1:], "hrut:n:", ["help", "before=", "after="])
    # print(opts, args)
    for o, a in opts:
        if o in ("-h", "--help"):
            print("usage: nahw1-2_0656088.py [-h] [-u] [--after AFTER] [--before BEFORE] [-n N]")
            print("                          [-t T] [-r]")
            print("                          filename")
            print("")
            print("Auth log parser.")
            print("")
            print("positional arguments:")
            print("  filename    Log file path.")
            print("")
            print("optional arguments:")
            print("  -h, --help       show this help message and exit")
            print("  -u               Show failed login log and sort log by user .")
            print("  --after AFTER    Filter log after data. format YYYY-MM-DD-HH:MM:SS")
            print("  --before BEFORE  Filter log before data. format YYYY-MM-DD-HH:MM:SS")
            print("  -n N             Show only the user of most N-th times")
            print("  -t T             Show only the user of attacking equal or more than T times")
            print("  -r               Sort in reverse order")
            sys.exit()
        elif o == '-u':
            sort_by_user = True
        elif o == '--after':
            after = datetime.strptime(a, '%Y-%m-%d-%H:%M:%S')
        elif o == '--before':
            before = datetime.strptime(a, '%Y-%m-%d-%H:%M:%S')
        elif o == '-n':
            max = int(a)
        elif o == '-t':
            min = int(a)
        elif o == '-r':
            reverse = True
    filepath = args[-1]
    # print("filepath: ", filepath)
    # print("sort_by_user: ", sort_by_user)
    # print("after: ", after)
    # print("before: ", before)
    # print("max: ", max)
    # print("min: ", min)
    # print("reverse: ", reverse)

    # open file
    file = open(filepath, "r")

    # read and store sshd log
    logs = []
    while True:
        line=file.readline()
        if not line:
            break
        if 'nvalid user' in line:
            logs.append(Log(line))

    # filter by time (before & after)
    filtered_logs = filter(lambda l: l.time > after and l.time < before, logs)

    # count display times of each users
    users = list(map(lambda l: l.user, filtered_logs))
    sum_dic = {}
    for user in users:
        sum_dic[user] = (sum_dic[user] + 1) if user in sum_dic else 1

    # turn dic to list
    sum_list = []
    for user in sum_dic:
        sum_list.append([user, sum_dic[user]])

    filtered_sum_list = filter(lambda l: l[1] >= min and l[1] <= max, sum_list)

    # determine sort method (is reverse or sort by user name)
    if sort_by_user:
        table_data = sorted(filtered_sum_list, key=lambda user: user[0], reverse=reverse)
    else:
        table_data = sorted(filtered_sum_list, key=lambda user: user[1], reverse=not reverse)

    # draw list as table on console
    draw_summary(table_data)

    file.close()

if __name__ == "__main__":
    main()
