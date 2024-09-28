#!/usr/bin/env python3

############### services ########################
#https://circuitdigest.com/forums/arduino-and-raspberry-pi/automatically-run-python-script-raspberry-pi-specific-time-tips-and-guide

from decouple import config, Csv
import requests
from datetime import datetime, timedelta
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

print('start program: ', datetime.today())

next_school_day = datetime.today().now() + timedelta(1)

while next_school_day.weekday() > 4:   # 5 = Saturday, 6 = Sunday
    next_school_day = next_school_day + timedelta(1)

s = requests.Session()
url = config('website_login', default='')
answer = s.get(url)
cookies = dict(answer.cookies)
answer = s.post(url, data={'_username':config('website_user', default=''), '_password':config('website_pass', default='')}, verify=True, cookies=cookies)
answer = s.get(config('website_url', default=''))  # +'S-' + next_school_day.strftime('%Y-%m-%d') + '.htm')

if answer.status_code == 200:
    print('Vertretungsplan vorhanden')

    #http://docs.python.org/howto/regex.html
    #https: // regex101.com /
    table_string = re.findall('.*?Klasse\(n\).*?(<tr class.*?</table>)', answer.text, re.DOTALL)
    text_list = re.findall('.*?<tr.*?<td.*?>(.*?)<', table_string[0])

    pupils_class = config("pupils_class", cast=Csv())
    pupils_address = config("pupils_address", cast=Csv())
    pupils = dict(zip(pupils_class, pupils_address))

    for klasse, address in pupils.items():
        entry_found = False
        for text in text_list:
            print('target text: ', text)
            if len(klasse)<3 : print('error: wrong class format -> ', klasse); exit();
            if klasse[:2] in text and klasse[2] in text:  # eg. check for '05' and 'a' in text
                print('entry found in: ', text)
                entry_found = True

        if entry_found:
            print('Eintrag für Klasse ' + klasse + ' gefunden.')

            ######################### send mail #########################
            #https://www.youtube.com/watch?v=qYxH3WzaOmk
            #https://stackoverflow.com/questions/882712/sending-html-email-using-python

            mail                  = MIMEMultipart('alternative')
            mail['Subject']       = 'Vertretungsplan für Klasse ' + klasse + ' heute' #den " + next_school_day.strftime('%d-%m-%Y')
            mail['From']          = config('sender_mailaddress', default='')
            mail['To']            = address
            mail.attach(MIMEText(answer.text, 'html'))

            sender = smtplib.SMTP(config('sender_smtp', default=''), 587)
            sender.ehlo()
            sender.starttls()
            sender.ehlo()

            sender.login(config('sender_user', default=''), config('sender_pass', default=''))
            sender.send_message(mail)
            sender.close()

            print('Eintrag für Klasse ' + klasse + ' wurde versendet.')
        else:
            print('Keine Vertretung für Klasse ' + klasse + '.')
