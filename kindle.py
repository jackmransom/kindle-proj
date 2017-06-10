import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import datetime

import codecs
try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/gmail.readonly']
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Bedside Kindle'

def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.bsk/credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'googlecreds.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:
            credentials = tools.run(flow, store)
    return credentials

def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    cal_service = discovery.build('calendar', 'v3', http=http)

    output = codecs.open('base.svg', 'r', encoding='utf-8').read()
    
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    events_result = cal_service.events().list(
            calendarId='primary', timeMin=now, maxResults=3, singleEvents=True,
            orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('Oops')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))

    mail_service = discovery.build('gmail', 'v1', http=http)
    mail_result = mail_service.users().threads().list(userId='me', maxResults=3, q='label:UNREAD').execute()
    threads = []

    if 'threads' in mail_result:
        threads.extend(mail_result['threads'])
    ids = []
    headers = ['From', 'Subject']
    for thread in threads:
        ids.append(thread['id'])
    message_headers = []
    for id in ids:
        message = mail_service.users().messages().get(userId='me', id=id, format="metadata", metadataHeaders=headers).execute()
        message_headers.append(message['payload']['headers'][0])
    for message_header in message_headers:
        print(message_header['name'] + message_header['value'])

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday!', 'Saturday', 'Sunday']
    output = output.replace('CURRENT_DAY', days[datetime.datetime.today().weekday()])

    try:
        output = output.replace('CAL_ONE', events[0]['start']['dateTime'] + ' - ' + events[0]['summary'])
        output = output.replace('CAL_TWO', events[1]['start']['dateTime'] + ' - ' + events[1]['summary'])
        output = output.replace('CAL_THREE', events[2]['start']['dateTime'] + ' - ' + events[2]['summary'])
    except IndexError:
        print("Oops")
    try:
        output = output.replace('MAIL_ONE', message_headers[0]['value'])
        #output = output.replace('MAIL_TWO', message_headers[1]['value'])
        #output = output.replace('MAIL_THREE', message_headers[2]['value'])
    except IndexError:
        print("Oops")

    codecs.open('kindle-output.svg', 'w', encoding='utf-8').write(output)

if __name__ == '__main__':
    main()
