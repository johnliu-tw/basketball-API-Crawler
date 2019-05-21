import sys
import time
import os
import traceback 

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup 
import pymysql

import setting

options = Options()
options.add_experimental_option( "prefs",{'profile.managed_default_content_settings.javascript': 2})
options.add_argument('--disable-gpu') 
driver = webdriver.Chrome(os.getcwd() + "/chromedriver", options = options)
driver2 = webdriver.Chrome(os.getcwd() + "/chromedriver", options = options)
driver3 = webdriver.Chrome(os.getcwd() + "/chromedriver", options = options)

DB_HOST = os.getenv("db_host")
DB_USER = os.getenv("db_user")
DB_PASSWORD = os.getenv("db_password")
DB_SCHEMA = os.getenv("db_schema")

db = pymysql.connect(DB_HOST,DB_USER,DB_PASSWORD,DB_SCHEMA)
cursor = db.cursor()
try:
    driver.get('''https://www.basketball-reference.com/teams/''')
    source_code = BeautifulSoup (driver.page_source, "html.parser")
    team_table = source_code.select("table[id='teams_active']")
    source_code2 = BeautifulSoup (str(team_table), "html.parser")
    teams_row = source_code2.find_all("tr")
    for i, team_row in enumerate(teams_row):
        if (i != 0): 
            if 'page' not in locals():
                sql = '''Select * FROM basketball_api.counters WHERE legend = 'NBA' and craw_type = 'team' '''
                cursor.execute(sql)
                db.commit()
                results = cursor.fetchall()
                page = int(results[0][4])
            print("page Num:" + str(page))  
            print("page index:" + str(i))
            if(page == i):
                source_code3 = BeautifulSoup (str(team_row), "html.parser")
                team_factor = source_code3.find_all("td")
                link = source_code3.find("th").find("a")['href'] if source_code3.find("th").find("a") != None else None
                if link == None:
                    page +=1 
                    sql = '''UPDATE basketball_api.counters SET page = {} WHERE legend = 'NBA'  and craw_type = 'team'; '''.format(page)
                    cursor.execute(sql)
                    db.commit()
                    continue
                driver2.get('''https://www.basketball-reference.com''' + link)
                source_code4 = BeautifulSoup (driver2.page_source, "html.parser")

                # Get team info 
                name = source_code3.find("th").find("a").text
                s_name = link[7:10]
                seasons = team_factor[3].text
                total_win = team_factor[5].text
                total_lost = team_factor[6].text
                playoff_count = team_factor[8].text
                championships = team_factor[11].text
                team_id = 9999

                # Check team length
                sql = '''Select * FROM basketball_api.nba_teams'''
                cursor.execute(sql)
                db.commit()
                results = cursor.fetchall()


                if len(results) != 31:            
                    # Insert team info to database
                    sql = '''INSERT INTO basketball_api.nba_teams 
                            (name, s_name, seasons, total_win, total_lost, playoff_count, championships) 
                            VALUES('{}','{}',{},{},{},{},{})'''.format(name, s_name, seasons, total_win, total_lost, playoff_count, championships)
                    cursor.execute(sql)
                    db.commit()
                    team_id = cursor.lastrowid
                    print(team_id)
                else:
                    # Query team info from database
                    sql = '''Select * FROM basketball_api.nba_teams WHERE s_name = '{}' '''.format(s_name)
                    print(sql)
                    cursor.execute(sql)
                    db.commit()
                    results = cursor.fetchall()
                    team_id = results[0][0]

                if 'count' in locals():
                    count = 1
                # Get team datas
                data_rows = source_code4.find(id=s_name).find_all("tr")
                for idx, data_row in enumerate(data_rows):
                    if idx != 0:
                        if 'count' not in locals():
                            sql = '''Select * FROM basketball_api.counters WHERE legend = 'NBA' and craw_type = 'team' '''
                            cursor.execute(sql)
                            db.commit()
                            results = cursor.fetchall()
                            count = int(results[0][3])
                        print(count)
                        if(count == idx): 
                            source_code5 = BeautifulSoup (str(data_row), "html.parser")
                            print(source_code5)
                            if source_code5.find_all("td")[0].text == "NBA":
                                season = source_code5.find("th").text[:4]
                                win = source_code5.find_all("td")[2].text
                                lost = source_code5.find_all("td")[3].text
                                srs = source_code5.find_all("td")[6].text
                                top_player_link = source_code5.find_all("a")[-1]['href']
                                
                                if 'player_count' not in locals():
                                    sql = '''SELECT * FROM nba_players'''
                                    cursor.execute(sql)
                                    db.commit()
                                    results = cursor.fetchall()
                                    player_count = len(results)

                                if player_count > 0:
                                    # get top player_id
                                    driver3.get('''https://www.basketball-reference.com''' + top_player_link)
                                    time.sleep(1)
                                    source_code5 = BeautifulSoup (driver3.page_source, "html.parser")
                                    player_name =  source_code5.find("h1").text

                                    sql = '''
                                    SELECT * FROM nba_players left join nba_player_datas on nba_players.id = nba_player_datas.player_id 
                                    WHERE name = "{}" and season = {} 
                                    '''.format(player_name, season)

                                    cursor.execute(sql)
                                    db.commit()
                                    results = cursor.fetchall()
                                    print(sql)
                                    
                                    top_player_id = results[0][0]

                                    sql = '''INSERT INTO basketball_api.nba_team_datas 
                                            (team_id, season, win, lost, srs, top_player_id) 
                                            VALUES({}, '{}','{}',{},{},{})'''.format(team_id, season, win, lost, srs, top_player_id)
                                    cursor.execute(sql)
                                    db.commit()
                                    print(season)
                                    
                                    count += 1
                                    sql = '''UPDATE basketball_api.counters SET count = {} WHERE legend = 'NBA'; '''.format(count)
                                    cursor.execute(sql)
                                    db.commit()
                page +=1 
                sql = '''UPDATE basketball_api.counters SET page = {} WHERE legend = 'NBA'  and craw_type = 'team'; '''.format(page)
                cursor.execute(sql)
                db.commit()
    driver.quit()
    driver2.quit()
    driver3.quit()
    db.close()
                        
except Exception as e:
    driver.quit()
    driver2.quit()
    driver3.quit()
    db.close()
    traceback.print_exc()