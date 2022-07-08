import warnings
warnings.filterwarnings("ignore") # i know that skipping ssl verify is bad
import requests, json, mysql.connector
import time, os
from bokeh.plotting import figure, save, output_file
from prettytable import PrettyTable
# load all the users i'm going to "track"
import multiprocessing as mp

# connect to MySQL but using an environment variable for the password ( ͡°( ͡° ͜ʖ( ͡° ͜ʖ͡°)ʖ ͡°) ͡°)
conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password=os.environ["MYSQL_PW"],
    database="devrant"
)
cursor = conn.cursor()
cursor.execute("SELECT name, uid FROM uid_name;")
uid_names = {}
for name_uid in cursor:
    uid_names[name_uid[1]] = name_uid[0]

# we need it in an hour or something but no reason to keep it up
conn.close()


def get_user_score(user):
#    time.sleep(2)  # sleep to not really ddos devRant api / maybe later
    print(user)
    # API request the app=3 is required by devRant API why? idk only 3 works
    user_request = requests.get("https://devrant.com/api/users/" + str(user) + "?app=3",verify=False) # skip ssl verify, because it sometimes says that the cert would be self signed??

    # error handling without panicking if something fails
    if user_request.status_code == 200:
        user_request_json = json.loads(user_request.text)
        if user_request_json["success"]:
            # return the relevant data to be stored in the results variable in the main method
            return (str(user), str(user_request_json["profile"]["score"]), user_request_json["profile"]["username"])
        else:
            print(user_request_json)
    else:
        print(user_request.status_code)
    return None

# Currently trying with multiprocessing
nproc = mp.cpu_count()
# iterate through the users and put the scores in to `results`
#results = [get_user_score(x) for x in uid_names]
with mp.Pool(processes=nproc) as mpP:
    results = mpP.map(get_user_score,[x for x in uid_names])


conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password=os.environ["MYSQL_PW"],
    database="devrant"
)
cursor = conn.cursor()
'''
Info about database:
    race(
        time DATETIME DEFAULT CURRENT_TIMESTAMP,
        uid INT FOREIGN KEY uid_name(uid),
        score INT
    )
    uid_name(
        uid INT,
        name TEXT
    )

'''
# insert each result if it was successfully returned from the api
for r in results:
    if r is not None:
        # update name, it may have changed
        cursor.execute("UPDATE uid_name SET name='" + r[2] + "' WHERE uid=" + r[0])
        # some weird SQL statement because i use FOREIGN KEY
        cursor.execute(
            "INSERT INTO race(uid,score) VALUES((SELECT uid FROM uid_name WHERE uid=" + r[0] + ")," + r[1] + ")")
conn.commit()

# now the data is stored in the database but how about some graphs to look at ＼(^o^)／

# first getting the latest name for each user_id so i can save the files accordingly
cursor.execute("SELECT name, uid FROM uid_name;")
uid_names = {}
for name_uid in cursor:
    uid_names[name_uid[1]] = name_uid[0]

cursor.execute("SELECT time,uid,score FROM race;")
xs = {}
ys = {}
# create for every user an x_axis entry and an y_axis entry
for x in cursor:
    if x[1] not in xs:
        xs[x[1]] = []
    if x[1] not in ys:
        ys[x[1]] = []
    xs[x[1]].append(x[0])
    ys[x[1]].append(x[2])

# Output the Score Difference since the start of logging
cursor.execute("SELECT (SELECT name FROM uid_name WHERE uid_name.uid = race.uid) as Name,(SELECT score FROM race as t WHERE t.time = MAX(race.time) AND t.uid = race.uid) - (SELECT score FROM race as tm WHERE tm.time = MIN(race.time) AND tm.uid = race.uid) as score_diff FROM race GROUP BY uid ORDER BY score_diff DESC;")
pt = PrettyTable()
pt.field_names = ["Username","Score Difference"]
for x in cursor:
    pt.add_row(x)

with open("/var/www/dr-race/!score_diff.txt","w+") as sdt:
    sdt.write(pt.get_string())


# we don't need the database anymore so goodbye
cursor.close()

# now creating the graph in html with the bokeh library
for u in xs:
    output_file(os.environ["DOCUMENT_ROOT"] + "/" + uid_names[u] + ".html")
    graph = figure(x_axis_type='datetime', sizing_mode='stretch_both')
    graph.line(xs[u], ys[u])
    save(graph)

conn.close()
