import sys
import time
import os
import traceback 
import urllib.request, json 
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import pymysql

import setting

options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu') 
driver = webdriver.Chrome(os.getcwd() + "/chromedriver", options = options)

DB_HOST = os.getenv("db_host")
DB_USER = os.getenv("db_user")
DB_PASSWORD = os.getenv("db_password")
DB_SCHEMA = os.getenv("db_schema")

db = pymysql.connect(DB_HOST,DB_USER,DB_PASSWORD,DB_SCHEMA)
cursor = db.cursor()

try:

    sql = '''SELECT * FROM basketball_api.sbl_players'''
    cursor.execute(sql)
    db.commit()
    u_players_list = cursor.fetchall()

    if len(u_players_list) == 0:
        # Get season list from choxue API
        driver.get('''https://sbl.choxue.com/stats''')
        seasons_id_list = []
        elements = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, 'sortable-menu')))
        for element in elements.find_elements_by_xpath(".//*"):
            if "例行賽" in element.text:
                seasons_id_list.append(element.get_attribute('value'))
        
        # Get player list from choxue API
        players_id_list = []
        for season in seasons_id_list:
            print(season)
            time.sleep(1)
            with urllib.request.urlopen("https://choxue.com/api/v1/v7/legacy/seasons/{}/players".format(season)) as url:
                players_data = json.loads(url.read().decode())
                for player_data in players_data:
                    players_id_list.append(player_data['player_id'])
        u_players_list = set(players_id_list)

        for player_id in u_players_list:
            sql = '''INSERT INTO basketball_api.sbl_players 
                    (id) 
                    VALUES('{}')'''.format(player_id)
            cursor.execute(sql)
            db.commit()


    # Insert player info to database
    for player in u_players_list:
        time.sleep(1)
        with urllib.request.urlopen("https://choxue.com/api/v1/v7/legacy/v2/players/{}".format(player[0])) as url:
            d = json.loads(url.read().decode())
            for k, v in d.items():
                if v is None and k != "birthday":
                    d[k] = "0"
                elif v is None and k == "birthday":
                    d[k] = "1900-01-01"
                
            sql = '''UPDATE basketball_api.sbl_players SET
                    name = '{}', height= {}, weight={}, birth='{}', position='{}'
                    where id = '{}' '''.format(d['name_alt'], d['height'], d['weight'], d['birthday'], d['career'][0]['position'], player[0])
            print(sql)
            cursor.execute(sql)
            db.commit()
            print(d['name_alt'])
            

            # Insert player data to database
            scopes = ['player_id','season','team_id', 'g', 'gs', 'sp','fg', 'fga', 'fgp','3p','3pa','3pp',
                        'ft','fta','ftp','orb','drb','trb','ast','stl','blk','tov','pf','pts']
            sql = '''INSERT INTO basketball_api.sbl_player_data ({}) VALUES '''.format(", ".join(scopes))
            idx = 1
            if len(d['career']) > 0:
                for d_row in d['career']:
                    if "中華" not in d_row['team_name_alt']:
                        if "Season" in d_row.get('season_name', "Not Exist"):
                            p_d = d_row['average']
                            sql += '''('{}','{}','{}',{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}),'''.format(d['id'], d_row['season_name_alt'],
                                        p_d['team_id'],p_d['gp'], p_d['gs'], p_d['seconds'],
                                        p_d['two_m'], p_d['two_a'], p_d['two_pct'], p_d['trey_m'], p_d['trey_a'], p_d['trey_pct'],
                                        p_d['ft_m'], p_d['ft_a'], p_d['ft_pct'], p_d['reb_o'], p_d['reb_d'], p_d['reb'],
                                        p_d['ast'], p_d['stl'], p_d['blk'], p_d['turnover'], p_d['pfoul'], p_d['points'])
                    if idx == len(d['career']):
                        sql = sql[:-1]
                    idx +=1  
                cursor.execute(sql)
                db.commit()
    driver.quit()
except Exception as e:
    driver.quit()
    db.close()
    traceback.print_exc()