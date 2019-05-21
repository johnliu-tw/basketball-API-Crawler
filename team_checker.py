import pymysql

db = pymysql.connect("localhost","root","password","basketball_api" )
cursor = db.cursor()
class TeamChecker():
 def __init__(self, team_name):
  # Check team data
  if team_name == "TRI" or team_name == "MLH" or team_name == "STL":
    self.result = "ATL"
  elif team_name == "NYN" or team_name == "NJN":
    self.result = "BRK"
  elif team_name == "CHH" or team_name == "CHA":
    self.result = "CHO"
  elif team_name == "FTW":
    self.result = "DET"
  elif team_name == "PHW" or team_name == "SFW":
    self.result = "GSW"
  elif team_name == "SDR":
    self.result = "HOU"
  elif team_name == "BUF" or team_name == "SDC":
    self.result = "LAC"
  elif team_name == "MNL":
    self.result = "LAL"
  elif team_name == "VAN":
    self.result = "MEM"
  elif team_name == "NOH" or team_name == "NOK":
    self.result = "NOP"
  elif team_name == "SEA": 
    self.result = "OKC"
  elif team_name == "SYR":
    self.result = "PHI"
  elif team_name == "ROC" or team_name == "CIN" or team_name == "KCO" or team_name == "KCK":
    self.result = "SAC"
  elif team_name == "NOJ":
    self.result = "UTA"
  elif team_name == "CHP" or team_name == "CHZ" or team_name == "BAL" or team_name == "CAP" or team_name == "WSB":
    self.result = "WAS" 
  else:
    self.result = team_name

  sql = '''Select * FROM basketball_api.nba_teams WHERE s_name = '{}' '''.format(self.result)
  cursor.execute(sql)
  db.commit()
  results = cursor.fetchall()
  self.result = results[0][0] if len(results) > 0 else 31

