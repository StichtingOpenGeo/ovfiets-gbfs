#!/usr/bin/python3

import json
import gzip
import sys
import zmq
import time
import os

basepath = '/home/projects/gbfs.openov.nl/htdocs/ovfiets'

plan = { "plan_id": "NORMAL", "name": "Dagtarief", "currency": "EUR", "price": 3.85, "is_taxable": 0, "description": "Dag tarief" }

regions = {}
station_informations = {}
station_statuses = {}

def openingHours(i):
    days = [None, 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    service = {}
    for day in i:
        startTime = day['startTime'] + ':00'
        endTime_hh, endTime_mm = day['endTime'].split(':')
        if day['closesNextDay']:
            endTime_hh = str(int(endTime_hh) + 24)
        endTime = ':'.join([endTime_hh, endTime_mm, '00'])

        h = startTime + '_' + endTime
        if h in service:
            service[h].add(days[day['dayOfWeek']])
        else:
            service[h] = set([days[day['dayOfWeek']]])

    rental_hours = []
    for k, days in service.items():
        start_time, end_time = k.split('_')
        rental_hours.append({ "user_types": ["member"], "days": list(days), "start_time": start_time, "end_time": end_time })

    return rental_hours

context = zmq.Context()
subscriber = context.socket(zmq.SUB)
subscriber.connect("tcp://127.0.0.1:6703")
subscriber.setsockopt_string(zmq.SUBSCRIBE, "/")

prev = 0

current = int(time.time())

json.dump({"last_update": current, "ttl": 3660, "data": { "nl": { "feeds": [ { "name": "system_information", "url": "http://gbfs.openov.nl/ovfiets/system_information.json" }, { "name": "station_information", "url": "http://gbfs.openov.nl/ovfiets/station_information.json" }, { "name": "station_status", "url": "http://gbfs.openov.nl/ovfiets/station_status.json" }] } } }, open("%s/gbfs.json" % (basepath,), "w"))
json.dump({"last_update": current, "ttl": 3660, "data": { "system_id": "ovfiets", "language": "nl", "name": "OV-fiets", "operator": "NS", "url": "http://ovfiets.nl", "timezone": "Europe/Amsterdam", "license_url": "https://creativecommons.org/licenses/by-sa/3.0/nl/" } }, open("%s/system_information.json" % (basepath,), "w"))
json.dump({"last_update": current, "ttl": 3600, "data": { "plans": [plan] } }, open('%s/system_pricing_plans.json' % (basepath,), 'w'))

while True:
    current = int(time.time())
    multipart = subscriber.recv_multipart()
    msg = (gzip.decompress(multipart[1]))
    contents = msg.decode('utf-8').replace('\n', '').replace('\r', '')
    locatie = json.loads(contents)

    if 'rentalBikes' not in locatie['extra']:
        continue


    locationCode = locatie['extra']['locationCode'].replace('/', '_').replace('.', '_')
    os.makedirs("%s/%s" % (basepath, locationCode,), exist_ok=True)

    fetchTime = int(locatie['extra']['fetchTime'])
    rentalBikes = int(locatie['extra']['rentalBikes'])
    name = locatie['name']
    description = name
    if 'description' in locatie:
        description = locatie['description']
    lat = float(locatie['lat'])
    lon = float(locatie['lng'])

    station_information = {'station_id': locationCode, 'region_id': locationCode, 'name': description, 'lat': lat, 'lon': lon, 'rental_methods': ['TRANSITCARD']}
    station_status = { 'stations': [{'station_id': locationCode, 'num_bikes_available': rentalBikes, 'num_docks_available': 1, 'is_installed': 1, 'is_renting': 1, 'is_returning': 1, 'last_reported': fetchTime}] }
    region = { "region_id": locationCode, "name": name }
    system = { "system_id": locationCode, "language": "nl", "name": "OV-fiets", "operator": "NS", "url": "http://ovfiets.nl", "timezone": "Europe/Amsterdam", "license_url": "https://creativecommons.org/licenses/by-sa/3.0/nl/" }

    station_informations[locationCode] = station_information
    station_statuses[locationCode] = station_status
    regions[locationCode] = region

    feeds = [ { "name": "system_information", "url": "http://gbfs.openov.nl/ovfiets/%s/system_information.json" % (locationCode,) }, { "name": "station_information", "url": "http://gbfs.openov.nl/ovfiets/%s/station_information.json"  % (locationCode,) }, { "name": "station_status", "url": "http://gbfs.openov.nl/ovfiets/%s/station_status.json"  % (locationCode,) } ]
    if 'openingHours' in locatie:
        feeds.append({ "name": "system_hours", "url": "http://gbfs.openov.nl/ovfiets/%s/system_hours.json"  % (locationCode,)})
        json.dump({"last_update": current, "ttl": 3600, "data": { "rental_hours": openingHours(locatie['openingHours']) } }, open('%s/%s/system_hours.json' % (basepath, locationCode,), 'w'))

    try:
        os.makedirs('%s/%s' % (basepath, locationCode,))
        json.dump({"last_update": current, "ttl": 3660, "data": { "nl": { "feeds": feeds } } }, open("%s/%s/gbfs.json" % (basepath, locationCode,), "w"))
        json.dump({"last_update": current, "ttl": 3660, "data": system }, open("%s/%s/system_information.json"  % (basepath, locationCode,), "w"))
        json.dump({"last_update": current, "ttl": 3600, "data": { "plans": [plan] } }, open('%s/%s/system_pricing_plans.json' % (basepath, locationCode,), 'w'))
        json.dump({"last_update": current, "ttl": 3600, "data": { "regions": [region] } }, open('%s/%s/system_regions.json' % (basepath, locationCode,), 'w'))
    except:
        pass

    json.dump({"last_update": current, "ttl": 3660, "data": { 'stations': [station_information] } }, open("%s/%s/station_information.json" % (basepath, locationCode,), "w") )
    json.dump({"last_update": current, "ttl": 60, "data": { 'stations': [station_status] } }, open("%s/%s/station_status.json" % (basepath, locationCode,), 'w'))

    if prev < (current - 60):
        json.dump({"last_update": current, "ttl": 3660, "data": { 'stations': list(station_informations.values()) } }, open("%s/station_information.json" % (basepath,), "w") )
        json.dump({"last_update": current, "ttl": 60, "data": { 'stations': list(station_statuses.values()) } }, open("%s/station_status.json" % (basepath,), 'w'))
        json.dump({"last_update": current, "ttl": 3600, "data": { "regions": list(regions.values()) } }, open('%s/system_regions.json' % (basepath,), 'w'))
        
        if len(regions.values()) > 50:
            prev = current

