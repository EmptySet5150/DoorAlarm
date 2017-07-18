# Import some needed libaries
import sqlite3
import RPi.GPIO as GPIO
from twilio.rest import Client  # For sms
from time import time
from time import sleep
from datetime import datetime

GPIO.setmode(GPIO.BOARD)  # Set to board numbering of the GPIO pins
doorSwitch = 11
buzzer = 15
dbConn = sqlite3.connect('door.db')  # Database file
dbC = dbConn.cursor()  # Database cursor
ACCOUNT_SID = "[Get your own at twilio.com]"  # Account info from twilio
AUTH_TOKEN = "[Get your own at twilio.com]"  # Account info from twilio

# Setup the GPIO pins
GPIO.setup(doorSwitch, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Use the pull up resistor on the board
GPIO.setup(buzzer, GPIO.OUT)
GPIO.output(buzzer, 0)  # Make sure the buzzer is off

doorStatus = 0
openTime = 0
dbTimeStamp = datetime.now().strftime('%y/%m/%d %H:%M:%S')
lastSend = 3600  # Used as a place holder
smsMsg = Client(ACCOUNT_SID, AUTH_TOKEN)  # Used for twilio 


# Connect to the database and insert time and status values. Then commit the changes
def saveDB(time, status):
    dbC.execute('INSERT INTO RDStatus (DateTime, Status) VALUES (?, ?)', (time, status))
    dbConn.commit()


# If the door is open for more than two minutes and I have not been notified 
# about it in the last hour send a txt message
def sendSMS():
    global lastSend
    sendOK = time() - lastSend
    if sendOK >= 3600:
        print("Sending SMS Message")
        lastSend = time()
        smsMsg.messages.create(to="+15555555555", from_="+15555555555", body="Refrigerator door is open!")


# If the table does not exist in the database create it
dbC.execute('CREATE TABLE IF NOT EXISTS RDStatus(DateTime DATETIME, Status TEXT)')

try:
    while True:
        #		Check to see if the GPIO pin is high and the door was closed
        if GPIO.input(doorSwitch) == 1 and doorStatus == 0:
            dbTimeStamp = datetime.now().strftime('%y/%m/%d %H:%M:%S')
            openTime = time()
            doorStatus = 1
            saveDB(dbTimeStamp, "Open")  # Save to database
        #		Check to see if the GPIO pin is high and the door was open
        if GPIO.input(doorSwitch) == 1 and doorStatus == 1:
            #			If the door has been open two minutes send a text message and sound the buzzer
            if time() - openTime >= 120:
                sendSMS()
                GPIO.output(buzzer, 1)
                sleep(5)
                GPIO.output(buzzer, 0)
                sleep(1)
            #			If the door has been open thirty seconds sound the buzzer
            if time() - openTime >= 30 and time() - openTime < 120:
                GPIO.output(buzzer, 1)
                sleep(1)
                GPIO.output(buzzer, 0)
                sleep(3)
            #		Check to see if the GPIO pin is low and the door was open
        if GPIO.input(doorSwitch) == 0 and doorStatus == 1:
            dbTimeStamp = datetime.now().strftime('%y/%m/%d %H:%M:%S')
            doorStatus = 0
            GPIO.output(buzzer, 0)
            saveDB(dbTimeStamp, "Closed")  # Save to database


# On keyboard interrupt cleanup the GPIO pins and close the connection to the database
except KeyboardInterrupt:
    GPIO.cleanup()
    dbC.close()
    dbConn.close()
