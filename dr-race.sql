# Get Score diff
SELECT (SELECT name FROM uid_name WHERE uid_name.uid = race.uid),(SELECT score FROM race as t WHERE t.time = MAX(race.time) AND t.uid = race.uid) - (SELECT score FROM race as tm WHERE tm.time = MIN(race.time) AND tm.uid = race.uid) as score_diff FROM race GROUP BY uid ORDER BY score_diff;
# Get being/end score
SELECT (SELECT name FROM uid_name WHERE uid_name.uid = race.uid) as username,(SELECT score FROM race as t WHERE t.time = MIN(race.time) AND t.uid = race.uid) as "Start Score", (SELECT score FROM race as tm WHERE tm.time = MAX(race.time) AND tm.uid = race.uid) as "End Score" FROM race GROUP BY uid ORDER BY username;
