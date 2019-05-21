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
    teams_list = [
        {'臺灣銀行籃球隊' : 'cr0isL0YbswVcjZwvdbXDw'}, 
        {'富邦勇士籃球隊' : 'LKb-wxsF4KzvGQZNL0Sr5Q"'}, 
        {'台灣啤酒籃球隊' : '0kjCxreDcS_FlWrax9n_NA'}, 
        {'金門酒廠籃球隊' : 'vrauM82i8Qx20vrKpCaGuQ'}, 
        {'裕隆納智捷籃球隊' : 'f_j06_rGHdr0Y8TIwVIUWg'}, 
        {'達欣工程籃球隊' : 'En38kkXybfyjNiTBUtuBVw'}, 
        {'璞園建築籃球隊' : 'F6UuyzvVzw0SAYXMxWVBWg'}]
    for team in teams_list:
        k = list(team.keys())[0]
        v = team[k]
        driver.get('''https://zh.wikipedia.org/wiki/{}'''.format(k))
        source_code = BeautifulSoup (driver.page_source, "html.parser")
        team_table = source_code.find("table", "sortable")
        print('''https://zh.wikipedia.org/wiki/{}'''.format(k))
        source_code2 = BeautifulSoup (str(team_table), "html.parser")
        teams_row = source_code2.find_all("tr")
        for idx, team_row in enumerate(teams_row):
            source_code3 = BeautifulSoup (str(team_row), "html.parser")
            if (idx != 0 and idx+1 != len(teams_row) and len(source_code3.find_all("td")) > 7): 
                team_factor = source_code3.find_all("td")  
                

                season = int(team_factor[0].text.split("-")[0])-2002
                win = team_factor[5].text
                lost = team_factor[6].text
                rank = team_factor[3].text[0]

                sql = '''INSERT INTO basketball_api.sbl_team_datas (team_id, season, win, lost, ranking) 
                VALUES('{}','S{}',{}, {}, {})'''.format(v, season, win, lost, rank)
                print(sql)
                cursor.execute(sql)
                db.commit()
            if(idx+1 == len(teams_row)):
                championships_text = source_code.find("table", "infobox").find_all("td")[-1].text.split(" ")[0]
                team_factor = source_code3.find_all("th")
                playoff_table = source_code.find_all("table", "wikitable")[1]
                
                playoff_row_count = 0
                for playoff_row in BeautifulSoup(str(playoff_table), "html.parser").find_all("tr"):
                    if len(playoff_row.find_all("td")) > 5:
                        playoff_row_count += 1


                total_win = team_factor[2].text
                total_lost = team_factor[3].text
                playoff_count = playoff_row_count
                print(championships_text)
                championships = championships_text[:championships_text.find('次')]

                sql = '''INSERT INTO basketball_api.sbl_teams
                    (id, name, total_win, total_lost, playoff_count, championships) 
                    VALUES('{}','{}',{},{}, {}, {})'''.format(v, k, total_win, total_lost, playoff_count, championships)
                print(sql)
                cursor.execute(sql)
                db.commit()

    driver.quit()

except Exception as e:
    driver.quit()
    db.close()
    traceback.print_exc()