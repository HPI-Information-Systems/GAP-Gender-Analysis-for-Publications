import os
import csv
import time
from datetime import datetime
from flask import Flask, request

app = Flask(__name__)


@app.route('/log_visitor', methods=['GET'])
def log_visitor():
    ip_address = request.remote_addr
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    log_file = os.environ.get('LOG_FILE', 'visitors.csv')

    with open(log_file, 'a', newline='') as csvfile:
        fieldnames = ['timestamp']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if csvfile.tell() == 0:
            writer.writeheader()

        writer.writerow({
            'timestamp': timestamp,
        })

    return 'Logged visitor', 200

@app.route('/log_graph_creation', methods=['GET'])
def log_graph_creation():
    # Get public ip address of the visitor
    research_areas = request.args.getlist('research_areas')
    publication_types = request.args.getlist('publication_types')
    venues = request.args.getlist('venues')
    continents = request.args.getlist('continents')
    countries = request.args.getlist('countries')
    author_position = request.args.getlist('author_position')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    log_file = os.environ.get('LOG_FILE_QUERIED_GRAPHS', 'queried_graphs.csv')

    with open(log_file, 'a', newline='') as csvfile:
        fieldnames = [
            'timestamp',
            'research_areas',
            'publication_types',
            'venues',
            'continents',
            'countries',
            'author_position',
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if csvfile.tell() == 0:
            writer.writeheader()

        writer.writerow({
            'timestamp': timestamp,
            'research_areas': research_areas,
            'publication_types': publication_types,
            'venues': venues,
            'continents': continents,
            'countries': countries,
            'author_position': author_position,
        })

    return 'Logged query', 200


if __name__ == '__main__':
    from waitress import serve
    print("Starting server...")
    print("Press Ctrl+C to exit")
    serve(app, host="0.0.0.0", port=6502)
    print("Server stopped")
