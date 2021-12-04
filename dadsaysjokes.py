# Read .env file
from dotenv import load_dotenv 
load_dotenv()

# Load required packages
import requests
import pandas as pd
import os
import smtplib, ssl

import prefect
from prefect import task, Flow

# Store secrets/keys to variables
twitterKey = os.environ.get('twitterKey')
smsapiKey = os.environ.get('smsapiKey')
gmailPass = os.environ.get('gmailPass')
smsSender = os.environ.get('smsSender')
smsRecipient = os.environ.get('smsRecipient')
emailSender = os.environ.get('emailSender')
emailRecipient = os.environ.get('emailRecipient')

@task
def dadsaysjokes_task():
    # Initiate Prefect logger
    logger = prefect.context.get("logger")

    ## Get jokes from Dadsaysjokes (and Mark Normand) Twitter
    headers = {
        'Authorization': f"Bearer {twitterKey}",
    }

    params = {
        'query': '-is:retweet -is:reply (from:Dadsaysjokes OR from:marknorm)',
        'max_results': 100
    }

    response = requests.get('https://api.twitter.com/2/tweets/search/recent', headers=headers, params=params)
    data = response.json()
    
    # Set dataframe to max column width
    pd.set_option('max_colwidth', None)
    
    # Store data in dataframe, convert to string, and remove special characters
    df = pd.DataFrame(data['data']).sample()
    joke = df['text'].to_string(index=False).replace("\\n", "\n").replace("&amp;", "and")

    logger.info("Jokes retrieved successfully.")
    
    ## Send joke by text
    params = {
        'apiKey': smsapiKey,
        'to': smsRecipient,
        'content': joke,
        'from': smsSender,
    }

    response = requests.get('https://platform.clickatell.com/messages/http/send', params=params)

    logger.info("SMS sent successfully.")

    ## Send joke by email
    smtp_server = "smtp.gmail.com"
    port = 587
    sender_email = emailSender
    password = gmailPass
    receiver_email = emailRecipient
    message = f"""Subject: Dadsaysjokes API\n\n{joke}"""

    # Create a secure SSL context
    context = ssl.create_default_context()

    # Login to server and send email
    server = smtplib.SMTP(smtp_server,port)
    server.starttls(context=context)
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, message)
    server.quit()

    logger.info("Email sent successfully.")

flow = Flow("dadsaysjokes-flow", tasks=[dadsaysjokes_task])

flow.register(project_name="dadsaysjokes")