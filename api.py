from nicelog.formatters import Colorful
import logging
import sys

import libs.sql as sql
import libs.sec as sec

import threading, asyncio, random, string, json
from flask import Flask, request, jsonify


logger = logging.getLogger('sql')
logger.setLevel(logging.DEBUG,)
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(Colorful(
                                message_inline=True, 
                                show_filename=False, 
                                show_function=False
                              ))
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


class Api:
    
    def __init__(self) -> None:

      self.config = json.loads(open('config.json', 'r').read())
      self.app = Flask(__name__)
      self.routes()
      self.encryption = sec.AESCipher(self.config['secret'])
      self.db = sql.Database(logger=logger)
      threading.Thread(target=self.run).start()

    def routes(self):

      @self.app.route("/api/v1/auth", methods=['POST'])
      def auth():
        try:
          decrypted_data = json.loads(str(self.encryption.decrypt(request.json['data'])))
        except:
          return self.encryption.encrypt("UwU UwU UwU UwU UwU UwU UwU UwU UwU UwU UwU UwU").decode(), 200
        if not "uuid" in decrypted_data:
            return self.encryption.encrypt(json.dumps({"error":"task_id is required"})).decode(), 400
        if not "key" in decrypted_data:
            return self.encryption.encrypt(json.dumps({"error":"key is required"})).decode(), 400
        key_check = self.db.check_key(decrypted_data['key'], decrypted_data['uuid'])
        if key_check['success'] == True:
          return self.encryption.encrypt('{"data":200}').decode(), 200
        else:
          return self.encryption.encrypt('{"data":400}').decode(), 200

    def run(self) -> None:
        
      self.app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
   Api()