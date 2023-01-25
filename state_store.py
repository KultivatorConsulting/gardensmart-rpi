import os
import sqlite3

from datetime import datetime, timedelta

class StateStore:
  exe_dir = os.path.dirname(__file__)

  DB_FILENAME = exe_dir + '/db/gardensmart.db'

  def __init__(self, logger):
    db_conn = sqlite3.connect(self.DB_FILENAME)
    self.logger = logger

    self.logger.info('Opened database successfully')

    if (not self.if_table_exists(db_conn, 'ZoneValveState')):
      self.create_zone_valve_state_table(db_conn)

    db_conn.close()

  def if_table_exists(self, db_conn, table_name):
    cursor = db_conn.cursor()

    query = ''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='%s' ''' % (table_name)

    cursor.execute(query)

    if (cursor.fetchone()[0] == 1):
        return True

    db_conn.commit()
    return False

  def create_zone_valve_state_table(self, db_conn):
    db_conn.execute('''CREATE TABLE ZoneValveState
        (ID INT PRIMARY KEY NOT NULL,
        VALVE_ON_TIME INT,
        VALVE_OFF_TIME INT);''')
    db_conn.commit()
    self.logger.info('ZoneValveState table created successfully')

  def set_zone_valve_on(self, relay_id, duration):
    db_conn = sqlite3.connect(self.DB_FILENAME)
    query = '''INSERT INTO ZoneValveState
                      (ID, VALVE_ON_TIME, VALVE_OFF_TIME)
                      VALUES (?, ?, ?)
                      ON CONFLICT(ID) DO UPDATE SET VALVE_ON_TIME=?, VALVE_OFF_TIME=?;'''

    on_time = datetime.now()
    off_time = datetime.now() + timedelta(seconds=duration)
    data_tuple = (relay_id, on_time, off_time, on_time, off_time)

    db_conn.execute(query, data_tuple)

    db_conn.commit()
    db_conn.close()
    self.logger.info('ZoneValveState updated successfully')

  def clear_zone_valve(self, relay_id):
    db_conn = sqlite3.connect(self.DB_FILENAME)
    query = '''DELETE FROM ZoneValveState WHERE ID=?;'''

    data_tuple = (relay_id,)

    db_conn.execute(query, data_tuple)

    db_conn.commit()
    db_conn.close()
    self.logger.info('ZoneValveState removed successfully')

  def get_zone_valve_time_remaining(self, relay_id):
    db_conn = sqlite3.connect(self.DB_FILENAME)
    query = '''SELECT VALVE_ON_TIME, VALVE_OFF_TIME FROM ZoneValveState WHERE ID=?;'''

    data_tuple = (relay_id,)

    cursor = db_conn.cursor()
    cursor.execute(query, data_tuple)
    records = cursor.fetchone()

    if (records is not None):
      off_time = records[1]

      time_remaining = datetime.fromisoformat(off_time) - datetime.now()

      cursor.close()
      db_conn.commit()
      db_conn.close()
      self.logger.info('ZoneValveState retrieved')

      if (time_remaining.days == -1):
        return -1

      return time_remaining.seconds

    cursor.close()
    db_conn.commit()
    db_conn.close()
    self.logger.info('ZoneValveState not available')
    return None








