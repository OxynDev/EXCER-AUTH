import json
import sqlalchemy
import sqlite3
import random
import string
import time
import re
import logging


class Database:
    
    conn = None
    engine = None
    log = None
    

    def log_info(self, message: str) -> None:
        if self.logger != None:
            self.logger.info(message)
    def log_error(self, message: str) -> None:
        if self.logger != None:
            self.logger.error(message)


    def __init__(self, logger: logging = None) -> None:
        
        self.logger = logger

        try:
            self.conn = sqlite3.connect("database.db")
        except:
            self.log_error("Sqlite3 connection error")
            raise "Sqlite3 connection error"
        try:
            self.engine = sqlalchemy.create_engine('sqlite:///database.db?autocommit=true')
            self.econn = self.engine.connect()
        except:
            self.log_error("SqlAlchemy connection error")
            raise "SqlAlchemy connection error"

        self.metadata = sqlalchemy.MetaData()
        self.metadata.reflect(bind=self.engine)

        if not sqlalchemy.inspect(self.engine).has_table("users"):
            
            sqlalchemy.Table("users", self.metadata,
                sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True, nullable=False), 
                sqlalchemy.Column('date', sqlalchemy.Integer, default=round(time.time()*1000)),
                sqlalchemy.Column('key', sqlalchemy.String(32), nullable=False), 
                sqlalchemy.Column('discord_id', sqlalchemy.String), 
                sqlalchemy.Column('hwid', sqlalchemy.String),
                sqlalchemy.Column('hwid_limit', sqlalchemy.Integer),
            )
            self.metadata.create_all(self.engine)
            self.log_info(": Table created")
        else:
            self.log_info(": Database loaded")

    def check_hash_structure(self, hash):
        if len(hash) != 64:
            return False
        else:
            return bool(re.match("^[A-Za-z0-9]*$", hash))

    def check_key_structure(self, hash):
        if len(hash) != 32:
            return False
        else:
            return bool(re.match("^[A-Za-z0-9]*$", hash))


    def get_key(self, key: str):
        try:
            
            users = self.metadata.tables['users']
            query = sqlalchemy.select(users).where(users.c.key == key)
            result = self.econn.execute(query).fetchall()
            if result:
                return result
            else:
                return False
        except Exception as e:
            self.log_error(f": {e}")

    def add_user(self, discord_id: str, time_data: dict, hwid_limit: int = 1) -> None:
            
            date = None

            if time_data["type"] == "d":
                date = int(time.time()) + time_data['val'] * 24 * 60 * 60
            elif time_data["type"] == "h":
                date = int(time.time()) + time_data['val'] * 60 * 60

            try:
                int(discord_id)
            except ValueError:
                self.log_error(f": {discord_id} is not a valid discord id")
                return False
            
            users = self.metadata.tables['users']

            new_key = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase +string.digits) for _ in range(32))
                          
            query = (
                sqlalchemy.insert(users).
                values(key = new_key, 
                       discord_id = discord_id,
                       date = date,
                       hwid = json.dumps([]),
                       hwid_limit = hwid_limit
                       )
                )
            self.econn.execute(query)
            self.econn.commit()
            return new_key

    def add_hwid(self, key: str, new_hwid: str) -> None:

        if self.check_Hash(new_hwid) == False:
            return {"success": False, "message":"invalid hwid"}

        key_data = self.get_key(key)

        if key_data == False:
            return {"success": False, "message":"invalid key"}
        
        hwid_limit = key_data[0][5]
        old_hwid_list = json.loads(key_data[0][4])

        if len(old_hwid_list) < hwid_limit:
            
            try:
                old_hwid_list.append(new_hwid)
                new_list = json.dumps(old_hwid_list)
                users = self.metadata.tables['users']
                query = sqlalchemy.update(users).where(users.c.key == key).values(hwid = new_list)
                self.econn.execute(query)
                self.econn.commit()

                return {"success": True, "message":old_hwid_list}
            
            except Exception as e:
                self.log_error(f": {e}")
        else:
            return {"success": False, "message":"hwid limit {}/{}".format(len(old_hwid_list), hwid_limit)}

    def reset_hwid(self, key: str) -> None:

        key_data = self.get_key(key)
        
        if key_data == False:
            return {"success": False, "message":"invalid key"}
        
        hwid_limit = key_data[0][5]
        
        try:
            users = self.metadata.tables['users']
            query = sqlalchemy.update(users).where(users.c.key == key).values(hwid = "[]")
            self.econn.execute(query)
            self.econn.commit()

            return {"success": True, "message":"0/{}".format(str(hwid_limit))}
        
        except Exception as e:
            self.log_error(f": {e}")


    def check_key(self, key: str, hwid: str) -> bool:

        
        if self.check_hash_structure(hwid) == False:
            return {"success": False, "message":"invalid hwid"}
        
        if self.check_key_structure(key) == False:
            return {"success": False, "message":"invalid key"}
        
        key_data = self.get_key(key)
        if not key_data:
            return {"success": False, "message":"invalid key"}
        
        hwid_limit = key_data[0][5]
        if hwid_limit == 0:
            hwid_list = []
        else:
            hwid_list = json.loads(key_data[0][4])
        expiration_date = key_data[0][1]
        if expiration_date is not None and int(time.time()) > int(expiration_date):
            return {"success": False, "message":"time end"}

        if hwid not in hwid_list:
            if hwid_limit > 0 and len(hwid_list) >= hwid_limit:
                return {"success": False, "message": "invalid hwid"}
            else:
                self.add_hwid(key, hwid)
                return {"success": True, "message": "valid :D"}
        else:
            return {"success": True, "message": "valid :D"}
        

if __name__ == "__main__":
    
    #db = Database(#logger=logger)
    #print(db.check_key("uefRmzmIPnIrPNF34hl711cMoDX4JVyo","TESTESTETESTESTESTESTESTTESTESTESTESTESTTESTESTESTESTESTSTESTEST"))
    # res = db.update_balance("1111", 1.2 )
    # res = db.add_user("1111", {"type":"d","val":3}, 2)
    # print(res)
    # res = db.add_hwid("uefRmzmIPnIrPNF34hl711cMoDX4JVyo", "TESTESTETESTESTESTESTESTTESTESTESTESTESTTESTESTESTESTESTSTESTEST")
    # print(res)
    # print(db.reset_hwid("uefRmzmIPnIrPNF34hl711cMoDX4JVyo"))

    pass