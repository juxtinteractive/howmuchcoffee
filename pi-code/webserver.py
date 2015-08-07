#!/usr/bin/python

#based on https://gist.github.com/igniteflow/5436066

import BaseHTTPServer
import cgi
from pprint import pformat

PORT = 9000
FILE_TO_SERVE = 'log/w.log'


class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """
    For more information on CORS see:
    * https://developer.mozilla.org/en-US/docs/HTTP/Access_control_CORS
    * http://enable-cors.org/
    """
    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-type")

    def do_POST(self, *args, **kwargs):
        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
        postvars = {}

    def do_GET(self, *args, **kwargs):
        """ just for testing """
        self.send_response(200)
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-type")
        self.send_header("Content-type", "text/text")
        self.end_headers()
        body = ''
        with open(FILE_TO_SERVE) as f:
            body = f.read()
        self.wfile.write(body)
        self.wfile.close()


def httpd(handler_class=MyHandler, server_address=('0.0.0.0', PORT), file_=None):
    try:
        print "Server started on http://%s:%s/ serving file %s" % (server_address[0], server_address[1], FILE_TO_SERVE)
        srvr = BaseHTTPServer.HTTPServer(server_address, handler_class)
        srvr.serve_forever()  # serve_forever
    except KeyboardInterrupt:
        srvr.socket.close()


if __name__ == "__main__":
    """ ./webserver.py """
    httpd()