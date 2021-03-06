# -*- coding: utf-8 -*-
import SocketServer
import json
import re
import datetime
import time

"""
Variables and functions that must be used by all the ClientHandler objects
must be written here (e.g. a dictionary for connected clients)
"""

connectedClients = {}
userNames = []
chatHistory = []
helpText = "Available commands: login <username>, logout, message <msg>, names, help"


class ClientHandler(SocketServer.BaseRequestHandler):
    """
    This is the ClientHandler class. Every time a new client connects to the
    server, a new ClientHandler object will be created. This class represents
    only connected clients, and not the server itself. If you want to write
    logic for the server, you must write it outside this class
    """

    def returnTimeStamp(self):
        ts = time.time()
        return datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')

    def responsePayload(self, sender, response, content):
        response_payload = {
            'timestamp': self.returnTimeStamp(),
            'sender': None,
            'response': None,
            'content': None,
        }
        response_payload['sender'] = sender
        response_payload['response'] = response
        response_payload['content'] = content
        self.connection.send(json.dumps(response_payload))

    def handle(self):
        """
        This method handles the connection between a client and the server.
        """
        self.possible_requests = {
            'login': self.handle_login,
            'logout': self.handle_logout,
            'help': self.handle_help,
            'message': self.handle_message,
            'names': self.handle_names,
        }

        self.username = None
        self.ip = self.client_address[0]
        self.port = self.client_address[1]
        self.connection = self.request

        # Loop that listens for messages from the client
        while True:
            received_string = self.connection.recv(4096)
            try:
                payload = json.loads(received_string)
                request = payload.get('request')
                content = payload.get('content')
                self.checkRequest(request, content)
            except Exception:
                self.finish()

    def checkRequest(self, request, content):
        if request in self.possible_requests:
            if request == 'login':
                self.handle_login(self, content)
            elif request == 'logout':
                self.handle_logout(self, None)
            elif request == 'help':
                self.handle_help(self, None)
            elif request == 'message':
                self.handle_message(self, content)
            elif request == 'names':
                self.handle_names(self, None)
            else:
                unknownRequest = 'Unknown request: '+ request
                self.responsePayload('server', 'error', unknownRequest)


    def handle_login(self, username):
        if not re.match("^[A-Za-z0-9]+$", username):
            self.responsePayload('server', 'error', 'Username invalid, must contain only characters or numbers')
            return 0
        elif not (len(username) < 16 and len(username) > 0):
            self.responsePayload('server', 'error', 'Username invalid, too long or too short.')
            return 0
        elif username in userNames:
            self.responsePayload('server', 'error', 'Username already taken')
            return 0
        else:
            self.responsePayload('server', 'info', 'Name approved.')
            userNames.append(username)
            self.responsePayload('server', 'info', 'Login successful')
            connectedClients.update({self.username, self.connection})
            return 1

    def handle_names(self):
        onlineUsers = 'Online users: ' + ",".join(userNames)
        self.responsePayload('server', 'info', onlineUsers)


    def handle_logout(self):
        if self.username in userNames:
            userNames.remove(self.username)
            connectedClients.pop(self.username)
            self.responsePayload('server', 'info', 'Logout succesful.')
        else:
            self.responsePayload('server', 'error', 'Not already logged in.')

    def handle_help(self):
        self.responsePayload('server', 'info', helpText)

    def handle_message(self, message):
        if self.username in userNames:
            self.sendJsonPayloadToAll()
            self.responsePayload('server', 'info', 'Message sent to all.')
        else:
            self.responsePayload('server', 'error', 'Not logged in.')

    def sendJsonPayload(self, payload):
        self.connection.send(json.dumps(payload))

    def sendJsonPayloadToAll(self, payload):
        jSon = json.dumps(payload)
        for con in connectedClients.values():
            con.send(jSon)


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    """
    This class is present so that each client connected will be ran as a own
    thread. In that way, all clients will be served by the server.

    No alterations are necessary
    """
    allow_reuse_address = True


if __name__ == "__main__":
    """
    This is the main method and is executed when you type "python Server.py"
    in your terminal.

    No alterations are necessary
    """
    HOST, PORT = 'localhost', 9998
    print 'Server running...'

    # Set up and initiate the TCP server
    server = ThreadedTCPServer((HOST, PORT), ClientHandler)
    server.serve_forever()
