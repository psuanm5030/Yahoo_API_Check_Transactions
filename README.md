# Lambda Check Trans

A simple script deployed on AWS Lambda to check the Yahoo Fantasy Football API for league transactions.  Anytime adds/drops are completed, a SMS is sent to notify you.

## Pre-Requisites
* YDN Free Account.  You'll need to create an 'app' with yahoo.  [Go Here](https://developer.yahoo.com/apps/) and register and "Create an App".  Select "Installed Application" and give the App a name (feel free to fill out the other information). Select "Fantasy Sports" and "Read".  Hit "Create App".  Once approved (if there is a waiting period) you can click into this app and gather the "Client ID (Consumer Key)" and "Client Secret (Consumer Secret)".
* Twilio FREE account.  You'll need to gather the following information from them: "sid", "auth_token" and "twilio_number".
* AWS Free Tier account.  You must join AWS to deploy this script to.

## Setting up the enviornment
1. Ensure that you have virtualenv installed (if not, `run pip install virtualenv`)
2. Clone this project to your desktop.
3. In the terminal, navigate to this directory and create a virtual environment `virtualenv my_project` (change to whatever you want).  This is where python and the requisite packages will be installed.  Activate the virtualenv using `source my_project/bin/activate`.
4. Run `pip install -r requirements.txt` to install the packages necessary.  This will install the packages into your virtualenv within your project.
5. Run Locally first.  Run the "check_trans.py" script.  The console will automatically open up a browser window and ask you to authenticate.  Copy the 7 character code and paste into console.  This will create the "yahoo_creds.pkl" file which will be used indefinitely to refresh your tokens.
    - Be sure to setup the "config_example.yml" file.
    - Be sure to set `LOCAL_DEBUG = True` in the "check_trans.py" file.
6. Because AWS Lambda wants a .ZIP package (inclusive of the packages and scripts), you must create a .ZIP file.
    - First edit this "create_package.sh" script and replace "AWS_Lambda" with the name of your root directory.
    - In the root directory of your project, run the "create_package.sh" script.  This will zip up all the requisite files into a file named "package.zip".  This will be uploaded to AWS in a few steps.
7. Go to AWS Lambda and create a function.
    - Choose "Author from Scratch".
    - Give the function a name.
    - Select "Python 2.7" as your runtime.
    - Select a role or create one if necessary.  Sorry, cant give too much guidance here.
    - Click "Create Function"
8. Add triggers to your function.  I have setup my function to run every 15 minutes.
    - Select "CloudWatch Events" as a trigger.
    - Under "Configure Triggers" within "Rule" select "Create a new rule"
    - Give it a name and description.
    - Select "Schedule expression" and put "cron(0/15 * * * ? *)" (not the quotes) in the field.
    - Click "Add"
9. Select your function (above your triggers). Ensure the following:
    - For "Code entry type" select "Upload a .ZIP file".  Then  select/upload the "package.zip" file from your desktop.
    - For "Runtime" ensure "Python 2.7" is selected.
    - For "Handler" type "check_trans.lambda_handler"
10. Setup the Envioronment Variables for the function.  In the section, create the following Keys with Values:
    - DEBUG : False
    - CHECK_TIME : 15
    - SEND_SMS : True
    - LEAGUE_1 : INSERT YAHOO ID
    - LEAGUE_1_NAME : INSERT NAME (WHATEVER YOU WANT)
    - LEAGUE_2 : INSERT YAHOO ID (BLANK IF NO EXTRA LEAGUE)
    - LEAGUE_2_NAME : INSERT NAME (WHATEVER YOU WANT) (BLANK IF NO EXTRA LEAGUE)
    - YAHOO_CLIENT_SECRET : INSERT VALUE FROM YAHOO
    - YAHOO_CLIENT_ID : INSERT VALUE FROM YAHOO
    - TWILIO_AUTH_TOKEN : INSERT VALUE FROM TWILIO
    - TWILIO_TO : INSERT VALUE FROM TWILIO
    - TWILIO_SID : INSERT VALUE FROM TWILIO
    - TWILIO_NUMBER : INSERT VALUE FROM TWILIO
11. In Basic Settings, set "Timeout" value to 30 seconds or higher.
12. Thats it!  You can now click "save" and you should get texts every 15 mins.

## Not currently setup
* Transaction: 'Trades' - havent had time to test.
* Transaction: 'Commish' - unsure what this really means.

## Credits
https://andypi.co.uk/2016/07/20/using-aws-lambda-to-run-python-scripts-instead-of-local-cron/
https://github.com/andy-pi/toggl2slack
http://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html