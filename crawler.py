#!/usr/bin/python
# coding: utf-8

import datetime
import json
import urllib
from datetime import datetime

import demjson
import requests
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim

google_api = str("AIzaSyAF2Ft98cW7sspxxtbdiH3AnltCzGHcs-A")

geolocator = Nominatim()


def crawler():
    fileName = "output.json"
    url = 'https://events.uta.edu/calendar/day?order=rating';
    source_code = requests.get(url)
    plain_text = source_code.text
    soup = BeautifulSoup(plain_text, 'html.parser')
    target = open(fileName, 'w+')
    target.truncate()
    event_list=[]

    for link in soup.findAll('div', {'class': 'item event_item vevent'}):

        event = {}
        title_block = link.find('img',{'class':'img_big'})
        eventTitle = title_block.get('title')
        eventTitle = eventTitle.encode('ascii','ignore')
        event['Event'] = eventTitle

        event['Image'] = title_block.get('src')
        venue_block = (str)(link.find('div',{'class':'location'}).find('a'))
        st = "</i> "
        n= venue_block.split(st);
        venue = (n[-1].split('</a>'))[0]
        event['Venue'] = str(venue)

        # To strip room numbers from the address
        finalVenue = ''.join([i for i in venue if not i.isdigit()])

        location_block = link.find('div',{'class':'location'}).find('a')
        try:
            loc_url = location_block.get('href')
            loc_code = requests.get(loc_url)
            loc_text = loc_code.text
            loc_soup = BeautifulSoup(loc_text, 'html.parser')
            address=loc_soup.find('p', {'class': 'location'}).find('span').text
            #address= address+" UTA Arlington TX"
            print  address
            response = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address=' + address.encode(
                    'utf8') + '&key=AIzaSyB3TWajTjRv4cj8lScvfUNwh_4KwZU9MnI')

            resp_json_payload = response.json()
            #print(resp_json_payload['results'][0]['geometry']['location'])
            event['Latitude'] = resp_json_payload['results'][0]['geometry']['location']['lat']
            event['Longitude'] = resp_json_payload['results'][0]['geometry']['location']['lng']

        except:
            address = " UTA Arlington TX"
            response = requests.get(
                'https://maps.googleapis.com/maps/api/geocode/json?address='+ address.encode('utf8') + '&key=AIzaSyB3TWajTjRv4cj8lScvfUNwh_4KwZU9MnI')
            resp_json_payload = response.json()
            #print(resp_json_payload['results'][0]['geometry']['location'])
            print resp_json_payload
            event['Latitude'] = "32.7311"
            event['Longitude'] = "-97.1141"

        try:
            type_block = link.find('div',{'class':'event_filters'}).find('a').string
            event['Type'] = (str)(type_block)
        except:
            event['Type'] = "NA"


        time_block = link.find('abbr')
        eventTime=time_block.get('title')
        t = datetime.strptime(eventTime, '%Y-%m-%dT%H:%M:%S-06:00')
        dateExtract = t.strftime("%I:%M %p    %m-%d-%Y")

        event['Time'] = dateExtract

        event_list.append(event)
        #print event

    event_dict = {'events': event_list}

    #Getting sensor locations
    #sensorUrl = "https://s3-us-west-2.amazonaws.com/eventnotifier/sensorLocations.json"
    sensorUrl = "https://mavspace.uta.edu/people/d/dx/dxj2757/sensorLocations.json"
    sensorRaw = urllib.urlopen(sensorUrl)
    event_dict['sensor'] = json.load(sensorRaw)
    #print event_dict['sensor']

    # Getting today's classes
    #classListUrl = "https://s3-us-west-2.amazonaws.com/eventnotifier/todaysClass.json"
    classListUrl = "https://mavspace.uta.edu/people/d/dx/dxj2757/todaysClass.json"
    classListRaw = urllib.urlopen(classListUrl)
    event_dict['class'] = json.load(classListRaw)

    f = demjson.encode(event_dict)
    #with open('result.json', 'w') as fp:
    #json.dump(event_dict, target)
    target.write(f)
    target.close()

def classScheduler():
    fileName = "todaysClass.json"

    def today_is(n):
        daysOfWeek = {'0': 'Mo', '1': 'Tu', '2': 'We', '3': 'Th', '4': 'Fr', '5': 'Sa', '6': 'Su'}
        return daysOfWeek[str(n)]

    target = open(fileName, 'w+')
    target.write('[')
    target.truncate()

    url = "https://mavspace.uta.edu/people/d/dx/dxj2757/classList.json"
    response = urllib.urlopen(url)
    data = json.load(response)
    event = {}
    flag = 0

    for i in data:
        s = i['Timing']
        temp = s.split(' ')
        day = datetime.today().weekday()  # Return the day of the week as an integer, where Monday is 0 and Sunday is 6
        l = len(temp[0])
        class_day_list = []
        class_days = temp[0]
        while (l > 0):
            class_day_list.append(class_days[l - 2:l])
            l = l - 2;
        n = 0
        while (n < len(class_day_list)):
            if (today_is(day) == class_day_list[n]):

                if (flag != 0):
                    target.write(',')
                flag = 1

                event['Timing'] = i['Timing']
                event['Course'] = i['Course']
                event['Section'] = i['Section']
                event['Classroom'] = i['Classroom']
                t = str(i['Classroom']).split(" ")[0]
                address = t + " UTA Arlington TX"
                response = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address=' + address.encode(
                    'utf8') + '&key=AIzaSyB3TWajTjRv4cj8lScvfUNwh_4KwZU9MnI')
                resp_json_payload = response.json()
                try:
                    event['Latitude'] = resp_json_payload['results'][0]['geometry']['location']['lat']
                    event['Longitude'] = resp_json_payload['results'][0]['geometry']['location']['lng']
                except:
                    event['Latitude'] = ""
                    event['Longitude'] = ""
                event['Professor'] = i['Professor']
                event['Start Time'] = temp[1] + " " + temp[2]
                json.dump(event, target)
            n = n + 1

    target.write(']')
    target.close()

def classCrawler():
    fileName = "classList.json"

    url = 'https://cse.uta.edu/current-students/2016/fall-2016-courses.php';
    source_code = requests.get(url)
    plain_text = source_code.text
    soup = BeautifulSoup(plain_text, 'html.parser')
    target = open(fileName, 'w+')
    target.write('[')
    target.truncate()
    flag=0;

    event = {}

    link = soup.find('table', {'class': 'borderless-table'})
    table_body = link.find('tbody')
    rows = table_body.find_all('tr')

    for row in rows:

        cols = row.find_all('td')
        if len(cols)==1:
            course = cols[0].get_text().strip()
        else:
            if (flag != 0):
                target.write(',')
            flag = 1

            event['Course'] = course
            event['Section'] = cols[0].get_text()
            event['Timing'] = cols[1].get_text()
            event['Classroom'] = cols[2].get_text()
            event['Professor'] = cols[3].get_text()
            json.dump(event, target)

    target.write(']')
    target.close()


classCrawler()
classScheduler()
crawler()
