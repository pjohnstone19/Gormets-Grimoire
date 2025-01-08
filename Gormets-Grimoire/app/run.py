import logging
from backend.controller import app

#logging configuration
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)10s() ] %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
log = logging.getLogger('root')
log.setLevel(logging.DEBUG)

if __name__ == "__main__":
	app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
	app.run(host='0.0.0.0', port=8880, threaded=True, debug=True)
	log.debug("GORMET'S GRIMOIRE IS STARTING!!! --> login.html")
