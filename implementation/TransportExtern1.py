from multiprocessing import Process
from queue import Queue

from flask import Flask, request, Response


import socket
hostname = socket.gethostname()
port = 9013
app = Flask(__name__)


@app.route('/calc', methods=['GET', 'POST'])
def calculaPreu():
    print("request form : ")
    print(request.form.get("peso"))
    data = request.form.get("peso")
    extra = 0
    if int(data) > 5:
        extra += 2
    return str(extra)

if __name__ == '__main__':
    app.run(host=hostname, port=port)
