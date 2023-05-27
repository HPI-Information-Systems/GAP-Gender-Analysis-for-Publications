import os
import csv
import time
from datetime import datetime
from flask import Flask, request

app = Flask(__name__)


@app.route('/log_visitor', methods=['GET'])
def log_visitor():
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    fingerprint = f"{ip_address}_{user_agent}"
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    log_file = os.environ.get('LOG_FILE', 'visitors.csv')

    with open(log_file, 'a', newline='') as csvfile:
        fieldnames = ['timestamp', 'ip_address', 'user_agent', 'fingerprint']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if csvfile.tell() == 0:
            writer.writeheader()

        writer.writerow({
            'timestamp': timestamp,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'fingerprint': fingerprint
        })

    return 'Logged visitor', 200



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6502)
