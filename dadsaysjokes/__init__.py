import logging
import requests
import pandas as pd
import os
import smtplib, ssl
import logging
import azure.functions as func

# Store secrets/keys to variables
twitterKey = os.environ['twitterKey']
smsapiKey = os.environ['smsapiKey']
gmailPass = os.environ['gmailPass']
smsSender = os.environ['smsSender']
smsRecipient = os.environ['smsRecipient']
emailSender = os.environ['emailSender']
emailRecipient = os.environ['emailRecipient']

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Set dataframe to max column width
    pd.set_option('max_colwidth', None)

    ## Get jokes from Dadsaysjokes (and Mark Normand) Twitter
    headers = {
        'Authorization': f"Bearer {twitterKey}",
    }

    params = {
        'query': '-is:retweet -is:reply (from:Dadsaysjokes OR from:marknorm)',
        'max_results': 100
    }

    response = requests.get('https://api.twitter.com/2/tweets/search/recent', headers=headers, params=params)

    if response.ok:
        data = response.json()
    else:
        logging.info("Error querying Twitter API")
    
    # Store data in dataframe, convert to string, and remove special characters
    try:
        df = pd.DataFrame(data['data']).sample()
        joke = df['text'].to_string(index=False).replace("\\n", "\n").replace("&amp;", "and")
        joke = str(joke)
        logging.info("Jokes retrieved successfully.")
    except Exception as e:
        logging.info("Joke failed to copy into DataFrame " + e)
    
    ## Send joke by text
    params = {
        'apiKey': smsapiKey,
        'to': smsRecipient,
        'content': joke,
        'from': smsSender,
    }

    response = requests.get('https://platform.clickatell.com/messages/http/send', params=params)

    if response.ok:
        logging.info("SMS sent successfully.")
    else:
        logging.info("Error sending SMS. Please check log.")

    ## Send joke by email
    smtp_server = "smtp.gmail.com"
    port = 587
    sender_email = emailSender
    password = gmailPass
    receiver_email = emailRecipient
    message = f"""Subject: Dadsaysjokes API\n\n{joke}"""

    name = False

    try:
        # Create a secure SSL context
        context = ssl.create_default_context()
        # Login to server and send email
        server = smtplib.SMTP(smtp_server,port)
        server.starttls(context=context)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)
        server.quit()
        name = True
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.error("Email failed " + e)

    if name:
        return func.HttpResponse(f"Dad jokes function was completed. Jokes were sent successfully.")
    else:
        return func.HttpResponse("Error: the function did not complete. See error logs", status_code=500)
