import pymysql


sql = '''UPDATE basketball_api.counters SET count = {}, page ={}  WHERE legend = 'NBA' and craw_type = 'player'; '''.format(1, 1)
cursor.execute(sql)
db.commit()

sql = '''UPDATE basketball_api.counters SET count = {}, page ={}  WHERE legend = 'NBA' and craw_type = 'team'; '''.format(1, 1)
cursor.execute(sql)
db.commit()

sql = '''INSERT INTO `basketball_api`.`nba_teams` (`id`, `name`, `s_name`, `seasons`, `total_win`, `total_lost`, `playoff_count`, `championships`) VALUES ('31', 'Total', 'TOT', '99', '9999', '9999', '99', '99');
'''.format(1, 1)
cursor.execute(sql)
db.commit()