import sys
import time
import os
import re
import traceback 
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup 
import pymysql
import numpy as np

from team_checker import TeamChecker
import setting

options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu') 
driver = webdriver.Chrome(os.getcwd() + "/chromedriver", options = options)
driver2 = webdriver.Chrome(os.getcwd() + "/chromedriver", options = options)

DB_HOST = os.getenv("db_host")
DB_USER = os.getenv("db_user")
DB_PASSWORD = os.getenv("db_password")
DB_SCHEMA = os.getenv("db_schema")

db = pymysql.connect(DB_HOST,DB_USER,DB_PASSWORD,DB_SCHEMA)
cursor = db.cursor()
try:

    # This would enumerate nba-reference player page from a to z
    # params: page is for log what page this program is crawling
    for i in range(ord("a"), ord("z")+1):
        if 'page' not in locals():
            sql = '''Select * FROM basketball_api.counters WHERE legend = 'NBA' and craw_type = 'player' '''
            cursor.execute(sql)
            db.commit()
            results = cursor.fetchall()
            page = int(results[0][4])
        print(chr(page))  

        if(page == i):     
            driver.get('''https://www.basketball-reference.com/players/{}/'''.format(chr(i)))
            source_code = BeautifulSoup (driver.page_source, "html.parser")
            player_table = source_code.select("table[id='players']")
            source_code2 = BeautifulSoup (str(player_table), "html.parser")
            players_row = source_code2.find_all("tr")

            # This would open player page and crawler his data
            # params: count 
            # is for checking which row this programing is crawling now, so it should be initilized after open a new page 
            if 'count' in locals():
                count = 1
            for idx, player_row in enumerate(players_row):
                if (idx != 0): 
                    if 'count' not in locals():
                        sql = '''Select * FROM basketball_api.counters WHERE legend = 'NBA' and craw_type = 'player' '''
                        cursor.execute(sql)
                        db.commit()
                        results = cursor.fetchall()
                        count = int(results[0][3])
                    print(count)
                    if(count == idx):                     
                        source_code3 = BeautifulSoup (str(player_row), "html.parser")
                        player_factor = source_code3.find_all("td")
                        link = source_code3.find("th").find("a")['href']
                        driver2.get('''https://www.basketball-reference.com''' + link)
                        time.sleep(1)
                        source_code4 = BeautifulSoup (driver2.page_source, "html.parser")
                        
                        print(link)
                        # Get player info 
                        name =  source_code4.find("h1").text
                        start_year = player_factor[0].text
                        end_year = player_factor[1].text
                        position = player_factor[2].text
                        height = player_factor[3].text
                        weight = player_factor[4].text  if player_factor[4].text != "" else "0"
                        birth = player_factor[5]['csk'] if player_factor[5].text != "" else "19000101"
                        school = player_factor[6].text

                        # transform time format
                        datetime_object = datetime.strptime(birth, '%Y%m%d')
                        birth = datetime_object.strftime("%Y-%m-%d")

                        country = source_code4.find("span", "f-i").text if source_code4.find("span", "f-i") != None else "None"
                        
                        paragraphs = source_code4.find_all('p')

                        draft_team = ""
                        draft_pick = ""
                        draft_year = 0 

                        # Because there lots of formats for draft text data, divide they to different if block
                        for paragraph in paragraphs:
                            if "Draft:" in paragraph.text:
                                pick_index = [idx for idx, p in enumerate(paragraph) if "overall" in p]

                                # Old draft would picked twice 
                                if len(paragraph.select("a[href*='/teams']")) > 1:
                                    draft_team = paragraph.select("a[href*='/teams']")[1].text
                                    if len(paragraph.contents[8].split(" ")) > 5:
                                        draft_pick = paragraph.contents[8].split(" ")[5]
                                    else:
                                        draft_pick = "None"
                                    draft_year = paragraph.contents[9].text.split(" ")[0]
                                elif len(paragraph.contents[4].split(" ")) > 4:
                                    draft_team = paragraph.contents[3].text
                                    draft_pick = paragraph.contents[4].split(" ")[5]
                                    draft_year = paragraph.contents[5].text.split(" ")[0]
                                # supplemental draft
                                elif (len(pick_index)>0):
                                    draft_team = paragraph.contents[2].split(" ")[2] + paragraph.contents[2].split(" ")[3]
                                    draft_pick = paragraph.contents[2].split(" ")[4]
                                    draft_year = paragraph.contents[3].text.split(" ")[2]   
                                # name draft                                 
                                else:
                                    draft_team = paragraph.contents[3].text
                                    draft_pick = "name"
                                    draft_year = paragraph.contents[5].text.split(" ")[0]     
                            else:
                                pass                                                  

                        # Insert player info to database
                        sql = '''INSERT INTO basketball_api.nba_players 
                                (name, height, weight, birth, school, start_year, end_year, draft_team, draft_pick, draft_year, position, country) 
                                VALUES("{}",'{}',{},'{}',"{}",{},{},'{}','{}',{},'{}','{}')'''.format(name, height, weight, birth, school, start_year, end_year, draft_team, draft_pick, draft_year, position, country)
                        cursor.execute(sql)
                        db.commit()
                        player_id = cursor.lastrowid
                        print(player_id)

                        # Get player data
                        # Because player data columns are different in different periods, the label for data should be dynamic
                        data_rows = source_code4.find(id="per_game").find_all("tr")
                        origin_data_rows = []
                        origin_data_row = []
                        for idx, data_row in enumerate(data_rows):
                            source_code5 = BeautifulSoup (str(data_row), "html.parser")
                            if (idx == 0):
                                labels = source_code5.find_all("th")
                            elif (source_code5.find("th") == None):
                                continue
                            else: 
                                season = source_code5.find("th").text[:4]
                                if season == "Care":
                                    break
                                stats = source_code5.find_all("td")
                                if stats[2].text != "NBA" and stats[2].text != "BAA":
                                    continue
                                origin_data_row = [stat.text if stat.text != "" else 0 for stat in stats]
                                origin_data_row.insert(0, season)
                                origin_data_row.insert(0, player_id)    
                                origin_data_rows.append(tuple(origin_data_row))
                        
                        labels = [label.text.replace("%","p").lower().replace('tm','team_id') for label in labels]
                        labels.insert(0, 'player_id')
                        player_data = np.array(origin_data_rows,
                        dtype=[(label,np.str, 16) for label in labels]
                        )
                        for player_data_row in player_data:
                            result = TeamChecker(player_data_row['team_id'])
                            player_data_row['team_id'] = result.result

                        # Insert player data to database
                        scopes = ['player_id','season','team_id','age', 'g', 'gs', 'mp','fg', 'fga', 'fgp','3p','3pa','3pp',
                                'ft','fta','ftp','orb','drb','trb','ast','stl','blk','tov','pf','pts']
                        
                        valid_labels = [label for label in labels if label in scopes]

                        sql = '''INSERT INTO basketball_api.nba_player_datas ({}) VALUES '''.format(", ".join(valid_labels))
                        player_data = player_data[valid_labels]

                        idx = 1
                        if player_data.size > 0:
                            for player_row_data in player_data:
                                if idx != player_data.size:
                                    sql +=  "(" + ",".join(player_row_data) + "),"
                                else:
                                    sql +=  "(" + ",".join(player_row_data) + ")"
                                idx +=1  
                            cursor.execute(sql)
                            db.commit()


                        count += 1
                        sql = '''UPDATE basketball_api.counters SET count = {} WHERE legend = 'NBA' and craw_type = 'player'; '''.format(count)
                        cursor.execute(sql)
                        db.commit()
            page +=1 
            sql = '''UPDATE basketball_api.counters SET page = {} WHERE legend = 'NBA'  and craw_type = 'player'; '''.format(page)
            cursor.execute(sql)
            db.commit()
    driver.quit()
    driver2.quit()
    db.close()
                

except Exception as e:
    driver.quit()
    driver2.quit()
    db.close()
    traceback.print_exc()
    
                
            


            
            
