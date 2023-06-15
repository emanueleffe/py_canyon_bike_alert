# source: https://github.com/emanueleffe/py_canyon_bike_alert

import os, requests, re, sys, logging, smtplib
from time import sleep
from bs4 import BeautifulSoup

''' Endless script option (be careful!) '''
endless = False
wait_time = 120 # seconds

''' email config parameters '''
send_email = False # or False
smtp_user = 'your@email.com'
smtp_password = 'yoursmtppsw'
smtp_host = 'smtp.server.com'
smtp_port = 'smtp_port'
smtp_ssl = True # or False
smtp_from_email = 'sender'
smtp_to_email = 'receiver'
email_subject = 'Canyon Bike Alert notification'

''' telegram config parameters '''
send_tg_notif = True # or False
tg_bot_token = 'your bot token'
tg_chat_id = 'chat id with your bot'


""" Initialize logger """
""" Create log folder if doesn't exist """
if not os.path.exists('log'):
    os.makedirs('log')
logging.basicConfig(level=logging.INFO,
                    filename='log/canyon_bike_alert.log',
                    filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


def send_telegram_notification(message,markdown=False):
    md = ''
    if markdown:
        md = '&parse_mode=Markdown'
    url = f"https://api.telegram.org/bot{tg_bot_token}/sendMessage?chat_id={tg_chat_id}&text={message}&disable_web_page_preview=true" + md
    requests.get(url).json()


def send_email_notification(subject, message):
    """Send an email notification.

    message - The message to send as the body of the email.
    """
    if (smtp_ssl):
        smtp_server = smtplib.SMTP_SSL(smtp_host, smtp_port)
    else:
        smtp_server = smtplib.SMTP(smtp_host, smtp_port)

    smtp_server.ehlo()
    smtp_server.login(smtp_user, smtp_password)

    email_text = \
"""From: %s
To: %s
Subject: %s

%s
""" % (smtp_from_email, smtp_to_email, subject, message)
    
    smtp_server.sendmail(smtp_from_email, smtp_to_email, email_text.encode('ascii','ignore'))
    smtp_server.close()


def extract_data(response, desired_size):
    parsed_html = BeautifulSoup(response.text, features='lxml')
    response_text = parsed_html.body.find(attrs={'data-product-size':desired_size}).text
    response_text = re.sub(r"^\s+", "", response_text)
    response_text = re.sub('^ ','',response_text)
    response_text = re.sub("[\n]+", "\n", response_text)
    response_text = re.sub('\n ','\n',response_text)
    response_text = re.sub("[\n]+", "\n", response_text)
    return response_text


def extract_bikename(response):
    parsed_html = BeautifulSoup(response.text, features='lxml')
    bikename = parsed_html.body.find(attrs={'class':'heading heading--2 productDescription__productName xlt-pdpName'}).text.replace('\n','')
    return bikename


def has_website_changed(website_url, website_name, desired_size):
    response = requests.get(website_url)

    if (response.status_code < 200 or response.status_code > 299):
        return {'result': -1}
    
    bikename = extract_bikename(response)

    response_text = extract_data(response,desired_size)

    cache_filename = website_name + "_cache.txt"

    if not os.path.exists(cache_filename):
        file_handle = open(cache_filename, "w")
        file_handle.write(response_text)
        file_handle.close()
        return {'result': 0, 'bikename': bikename}

    file_handle = open(cache_filename, "r+")
    previous_response_text = file_handle.read()
    file_handle.seek(0)

    if response_text == previous_response_text:
        file_handle.close()

        return {'result': 0, 'bikename': bikename}
    else:
        file_handle.truncate()
        file_handle.write(response_text)
        file_handle.close()
        
        return {'result': 1, 'response_text': response_text, 'bikename': bikename}


def main():
    """ Command line parameters:
    1) bike url, eg: https://www.canyon.com/it-it/gravel-bikes/all-road/grail/al/grail-6/3092.html?dwvar_3092_pv_rahmenfarbe=GN%2FBK
                 beware: it must include the colour variant in the url, in this case: ?dwvar_3092_pv_rahmenfarbe=GN%2FBK
    2) path+filename where to store cache file eg 'cache/sandcolour' (check if the folder exists)
    3) colour_name of the bike, it will be used for notifications
    4) bike size to check (possible values: 2XS, XS, S, M, L, XL, 2XL) """
    url = sys.argv[1]
    cachefilename = sys.argv[2]
    colour_name = sys.argv[3]
    desired_bike_size = sys.argv[4].upper()

    message = ""

    """ Check if website has changed, if exception encountered send a notification.
        If also a notification fails, log the execution status """
    try:
        website_status = has_website_changed(url, cachefilename, desired_bike_size)
    except Exception as e:
        message = "*Error occured during the execution of the script for " + colour_name + " - Size: " + desired_bike_size + "* - url: " + url
        try:
            if send_tg_notif:
                send_telegram_notification(message)
            if send_email:
                send_email_notification(email_subject, message)
            logging.critical(message, exc_info=True)
        except Exception as e:
            message = message + " - Error occurred also while sending the notification"
            logging.critical(message, exc_info=True)
    
    """ website_status['result'] = -1 -> website response non 2xx 
                                    0 -> no change detected in webpage for desired bike size 
                                    1 -> change detected in webpage for desired bike size 
        notifications are sent in -1 and 1 cases. """
    if website_status['result'] == -1:
        message = "Error occurred while fetching the webpage, non 2XX response " + colour_name + " - Size: " + desired_bike_size + " - url: " + url
        try:
            if send_tg_notif:
                send_telegram_notification('*Error - Canyon Bike Alert*\n\n' + message)
            if send_email:
                send_email_notification(email_subject, '*Error - Canyon Bike Alert*\n\n' + message)
            logging.error(message, exc_info=True)
        except Exception as e:
            message = message + " - Error occurred also while sending the notification"
            logging.error(message, exc_info=True)
    elif website_status['result'] == 0:
        message = "No change for " + website_status['bikename'] + ' ' + colour_name
        logging.info(message)
    elif website_status['result'] == 1:
        message = '*~~~ WEBPAGE CHANGE DETECTED FOR ' + website_status['bikename'].upper() + ' ~~~\Colour: ' + colour_name.upper() + " - Size: " + desired_bike_size + '*'
        try:
            if send_tg_notif:
                send_telegram_notification(message + '\n\n' + website_status['response_text'] + '\n[Check the Canyon website here]('+url+')',markdown=True)
            if send_email:
                send_email_notification(email_subject, message + '\n\n' + website_status['response_text'] + '\nCheck the Canyon website here: '+url)
            logging.info(message.replace('\n',''))
        except Exception as e:
            message = 'Webpage change detected but an error occurred while sending the notification'
            logging.error(message, exc_info=True)


if __name__ == "__main__":
    first_pass = True
    while(endless or first_pass):
        try:
            first_pass = False
            main()
        except Exception as e:
            logging.error('',exc_info=True)
        if endless:
            sleep(wait_time)