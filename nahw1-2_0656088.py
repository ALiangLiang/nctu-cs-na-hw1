import sys
import re
import argparse
import texttable as tt
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

def main():

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', type=str, help="Log file path")
    parser.add_argument('-u', help="Summary failed login log sort log by user .", action="store_true")
    parser.add_argument("-after", type=lambda d: datetime.strptime(d, '%Y-%m-%d-%H:%M:%S'), help="Filter log after date. format YYYY-MM-DD-HH:MM:SS")
    parser.add_argument("-before", type=lambda d: datetime.strptime(d, '%Y-%m-%d-%H:%M:%S'), help="Filter log before date. format YYYY-MM-DD-HH:MM:SS")
    parser.add_argument("-n", type=int, help="Show only the user of most N-th times")
    parser.add_argument("-t", type=int, help="Show only the user of attacking equal or more than T times")
    parser.add_argument("-r", help="Sort in reverse order", action="store_true")
    args = parser.parse_args()

    sort_by_user = args.u or False
    after = args.after or datetime(1900, 1, 1)
    before = args.before or datetime(3000, 1, 1)
    max_number = args.n or None
    min = args.t or 0
    reverse = args.r or False
    file_path = args.filename
    # print("file_path: ", file_path)
    # print("sort_by_user: ", sort_by_user)
    # print("after: ", after)
    # print("before: ", before)
    # print("max_number: ", max_number)
    # print("min: ", min)
    # print("reverse: ", reverse)

    # open file
    file = open(file_path, "r")

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

    filtered_sum_list = filter(lambda l: l[1] >= min, sum_list)

    # determine sort method (is reverse or sort by user name)
    if sort_by_user:
        table_data = sorted(filtered_sum_list, key=lambda user: user[0], reverse=reverse)
    else:
        table_data = sorted(filtered_sum_list, key=lambda user: user[1], reverse=not reverse)

    if max_number:
        table_data = table_data[:max_number]

    # draw list as table on console
    draw_summary(table_data)

    file.close()

if __name__ == "__main__":
    main()
