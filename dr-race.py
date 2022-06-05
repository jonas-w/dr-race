import requests,json,mysql.connector
import time,os
from bokeh.plotting import figure, show, output_file

#load all active users with score over 300 i determined a few weeks ago
with open("./dr-active-user-with-over-300.json") as dauwo3:
    j = json.load(dauwo3)

def get_user_score(user):
    time.sleep(10) # sleep to not ddos devRant api
    
    # API request the app=3 is required by devRant API why? idk only 3 works
    user_request = requests.get("https://devrant.com/api/users/"+str(user)+"?app=3")
 
    #error handling without panicking if something fails
    if user_request.status_code == 200:
        user_request_json = json.loads(user_request.text)
        if user_request_json["success"]:
            # return the relevant data to be stored in the results variable in the main method
            return (str(user),str(user_request_json["profile"]["score"]),user_request_json["profile"]["username"])
        else:
            print(user_request_json)
    else:
        print(user_request.status_code)
    return None

if j is not None:
    # iterate through the users and put the scores in to `results`
    results = [get_user_score(x) for x in j]

    # connect to MySQL but using an environment variable for the password ( ͡°( ͡° ͜ʖ( ͡° ͜ʖ͡°)ʖ ͡°) ͡°)
    conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password=os.environ["MYSQL_PW"],
            database="devrant"
            )
    cursor = conn.cursor()
    '''
    Info about database:
        (
            time DATETIME DEFAULT CURRENT_TIMESTAMP,
            uid INT,
            score INT,
            name TEXT
        )

    '''
    # insert each result if it was successfully returned from the api
    for r in results:
        if r is not None:
            cursor.execute("INSERT INTO race(uid,score,name) VALUES("+r[0]+","+r[1]+",'"+r[2]+"')")      
 
    conn.commit()

    # now the data is stored in the database but how about some graphs to look at ＼(^o^)／
    
    # first getting the latest name for each user_id so i can save the files accordingly
    cursor.execute("SELECT DISTINCT name, uid FROM race ORDER BY time DESC;")
    uid_names = {}
    for name_uid in cursor:
        uid_names[name_uid[1]]=name_uid[0]
    
    cursor.execute("SELECT time,uid,score FROM race;")
    xs = {}
    ys = {}
    # create for every user an x_axis entry and an y_axis entry
    for x in cursor:
        if x[1] not in xs:
            xs[x[1]]=[]
        if x[1] not in ys:
            ys[x[1]]=[]
        xs[x[1]].append(x[0])
        ys[x[1]].append(x[2])

    # we don't need the database anymore so goodbye
    cursor.close()
    
    # now creating the graph in html with the bokeh library
    for u in xs:
        output_file(os.environ["DOCUMENT_ROOT"]+"/"+uid_names[u]+".html")
        graph = figure(x_axis_type='datetime',sizing_mode='stretch_both')
        graph.line(xs[u],ys[u])
        show(graph)
        
    conn.close()
