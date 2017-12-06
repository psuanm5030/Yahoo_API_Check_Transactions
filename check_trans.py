"""
PURPOSE: Script to load on AWS Lambda to report on transactions via text.

SETUP: Refer to the README.MD file.
"""

import webbrowser
import requests
import os
import xmltodict
import pickle
from datetime import datetime, timedelta
import json
import yaml
from sanction import Client as s_client
from twilio.rest import Client

# For local testing, turn LOCAL_DEBUG to true.
LOCAL_DEBUG = False
if LOCAL_DEBUG: # If true, gather variables from config.yml file
    stream = file('./config.yml', 'r')  # 'document.yaml' contains a single YAML document.
    creds = yaml.load(stream)
    creds = creds['all_creds']

    # Sets env variables
    os.environ["SEND_SMS"] = creds['SEND_SMS']
    os.environ["YAHOO_CLIENT_ID"] = creds['YAHOO_CLIENT_ID']
    os.environ["YAHOO_CLIENT_SECRET"] = creds['YAHOO_CLIENT_SECRET']
    os.environ["LEAGUE_1"] = creds['LEAGUE_1']
    os.environ["LEAGUE_2"] = creds['LEAGUE_2']
    os.environ["LEAGUE_1_NAME"] = creds['LEAGUE_1_NAME']
    os.environ["LEAGUE_2_NAME"] = creds['LEAGUE_2_NAME']
    os.environ["DEBUG"] = creds['DEBUG']
    os.environ["TWILIO_TO"] = creds['TWILIO_TO']
    os.environ["TWILIO_NUMBER"] = creds['TWILIO_NUMBER']
    os.environ["TWILIO_SID"] = creds['TWILIO_SID']
    os.environ["TWILIO_AUTH_TOKEN"] = creds['TWILIO_AUTH_TOKEN']
    os.environ["CHECK_TIME"] = creds['CHECK_TIME']

# Read in the Env Variables
# Yahoo
y_client_id = os.environ['YAHOO_CLIENT_ID']
y_client_secret = os.environ['YAHOO_CLIENT_SECRET']
redirect_uris = ["http://localhost", "urn:ietf:wg:oauth:2.0:oob"]
auth_uri = "https://api.login.yahoo.com/oauth2/request_auth"
token_uri = "https://api.login.yahoo.com/oauth2/get_token"
# Twilio
twilio_to = os.environ['TWILIO_TO']
twilio_number = os.environ['TWILIO_NUMBER']
twilio_sid = os.environ['TWILIO_SID']
twilio_auth_token = os.environ['TWILIO_AUTH_TOKEN']
# Other
check_time = int(os.environ['CHECK_TIME'])
send_sms = os.environ['SEND_SMS']

resource_endpoint='https://fantasysports.yahooapis.com/fantasy/v2'
PKL_NAME = 'yahoo_creds.pkl'
league_1 = os.environ['LEAGUE_1']
league_2 = os.environ['LEAGUE_2']
league_1_name = os.environ['LEAGUE_1_NAME']
league_2_name = os.environ['LEAGUE_2_NAME']


def access():
    """
    Simply connect to yahoo API to get token and store in pickle.
    :return: Returns the auth object
    """
    # instantiating a client to process OAuth2 response
    c = s_client(auth_endpoint=auth_uri,
               token_endpoint=token_uri,
               client_id=y_client_id,
               client_secret=y_client_secret)

    # Authorize and get the token
    auth_uri_r = c.auth_uri(redirect_uri='oob')
    webbrowser.open(auth_uri_r)
    auth_code = raw_input('Enter the auth code: ')

    # Grab the Token
    c.request_token(redirect_uri='oob', code=auth_code)

    # Store the Token Details
    print 'storing tokens...'
    with open(PKL_NAME, 'wb') as f:
        pickle.dump(c, f)

    return c

def refresh():
    """
    Refresh the available authorization object (stored in a pickle)
    :return: Returns the auth object
    """
    # Load the Pickle
    with open(PKL_NAME, 'rb') as f:  # Load the pickle
        c = pickle.load(f)

    c.request_token(grant_type='refresh_token', refresh_token=c.refresh_token)
    return c

def test_something(token):
    """
    Simple function to test API connection
    :param token: Yahoo API Token
    :return:
    """
    headers = {"Authorization": "bearer " + token,
               "format": "json"}
    url = resource_endpoint + '/league/359.l.67045'
    r = requests.get(url, headers=headers)
    details = xmltodict.parse(r.content)
    return details['fantasy_content']['league']

def send_sms(body):
    """
    Send a SMS with body details.
    :param body: string to send as SMS
    :return: none
    """
    client = Client(twilio_sid, twilio_auth_token)

    messages = client.messages.create(body=body,
                                     from_=twilio_number,
                                     to=twilio_to)

def send_query(url,token):
    """
    Makes request to API.
    :param url: e.g., 'https://fantasysports.yahooapis.com/fantasy/v2/league/359.l.67045'
    :param token: Yahoo API Token
    :return: dictionary response
    """
    headers = {"Authorization": "bearer " + token,
               "format":"json"}
    # url = 'https://fantasysports.yahooapis.com/fantasy/v2/league/359.l.67045'
    r = requests.get(url, headers=headers)
    details = xmltodict.parse(r.content) # in dictionary formats
    d1 = json.dumps(details)
    d2 = json.loads(d1) # in json format - to be used with object path
    return d2

def get_league_trans(league_key, token, time_elapsed_mins):
    """
    Check the transactions based upon league.
    :param league_key: key in the form of "371.l.83721"
    :param token: Yahoo API Token
    :param time_elapsed_mins: int - Minutes to consider a transaction for notification
    :return: none
    """
    url = resource_endpoint + '/league/{}/transactions'.format(league_key)
    details = send_query(url,token)
    details = details['fantasy_content']['league']['transactions']['transaction']
    if league_key == league_1:
        league_name = league_1_name
    else:
        league_name = league_2_name
    # Keep only those occuring in the last
    # todo check on the 'trade' type of transaction.  un-tested.
    for d in details:
        if d['type'] == 'commish':
            print 'Commish transaction - ignore.'
            continue
        t = datetime.fromtimestamp(int(d['timestamp'])) #.strftime('%Y-%m-%d %H:%M:%S')
        elapsed = datetime.now() - t
        elapsed_minutes = (elapsed.days * 1440) + (elapsed.seconds / 60.0)
        if elapsed_minutes <= time_elapsed_mins:
            try:
                plys = d['players']['player']
                for p in plys:
                    if p['transaction_data']['type'] == 'add':
                        team_name = p['transaction_data']['destination_team_name']
                    else:
                        team_name = p['transaction_data']['source_team_name']
                    body = '~{}: {} ({}-{}) was just {}ed by {}.  Time since move: {}.'.format(
                        league_name,
                        p['name']['full'],
                        p['editorial_team_abbr'],
                        p['display_position'],
                        p['transaction_data']['type'],
                        team_name,
                        str(int(elapsed_minutes)) + ' mins')
                    print 'Sending an SMS with this text: {}'.format(body)
                    if send_sms == 'True': # send SMS if noted
                        send_sms(body)
            except:
                print 'error'
                if send_sms == 'True':  # send SMS if noted
                    send_sms('Error on Transaction - might be commish or something else other than add / drop.')

    return

def lambda_handler(event, context):
    """
    AWS function that is called by the Lambda runtime.
    :param event: not used
    :param context: not used
    :return: none
    """
    if os.environ['DEBUG'] == 'True':
        send_sms('Lambda Function Run...')

    # Get the tokens
    try:
        print 'Refreshing existing tokens...'
        c = refresh()
    except:
        print 'Couldnt refresh... please authorize...'
        c = access()

    # detail = test_something(c.access_token)
    print 'league_1 Check initated...'
    get_league_trans(league_1,c.access_token,check_time)
    if league_2 != '':
        print 'league_2 Check initated...'
        get_league_trans(league_2,c.access_token,check_time)
    print 'Completed check.'

if __name__ == '__main__':
    # Try to refresh tokens, else request auth.
    # todo Make it so it doenst have to refresh unless its expired?
    try:
        print 'Refreshing existing tokens...'
        c = refresh()
    except:
        print 'Couldnt refresh... please authorize...'
        c = access()

    # detail = test_something(c.access_token)

    # Run
    get_league_trans(league_1, c.access_token, check_time)
    if league_2 != '':
        get_league_trans(league_2, c.access_token, check_time)
    print 'Completed MANUAL check.'