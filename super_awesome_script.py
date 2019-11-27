import serial
import time
import psutil
import datetime

#THe recorder's responses for acknowledged/not-acknowledge
ack = str(b"\x06")
nack = str(b"\x15")

#This replaces the ack/nack strings and new-line characters with human-readable ones
def readnprint():   #TODO Make this actually work :p
    s = str(ser.read(125))
    s = s.replace("\r", "\n")
    s = s.replace(ack, "ACK")
    s = s.replace(nack, "NACK")
    print (s)
    return

#This sets the time for the internal clock on the recorder
def settime():
    print("INFO: Setting Time...")
    DT = datetime.datetime.now() #Get the time
    while DT.second != 0: #Wait until we're right at the start of a new minute, bc the recorder doesn't use seconds
        DT = datetime.datetime.now() #Get the time
    YY = "{0:0=2d}".format(abs(DT.year) % 100)
    MM = "{0:0=2d}".format(DT.month)
    DD = "{0:0=2d}".format(DT.day)
    hh = "{0:0=2d}".format(DT.hour)
    mm = "{0:0=2d}".format(DT.minute)
    date_str = ("@0Dt" + str(YY) + str(MM) + str(DD) + str(hh) + str(mm) + "\r").encode('utf-8') #Change this into the format the recorder understands
    #print(date_str)
    ser.write(date_str)
    return

print("INFO: Script loaded")

#Below are the serial command strings for the recorder
on = b"@023PW\r"
off = b"@02312\r"

play = b"@02353\r"
stop = b"@02354\r"
rec = b"@02355\r"

rec_off = True

time_count = 0

ser = serial.Serial('COM3', 9600, timeout=1)    #Open the serial connection on COM3
bat = psutil.sensors_battery()                  #Load battery status object

print("INFO: Serial port open, battery status loaded")

time.sleep(1)

#Just in case this was already running earlier, flush the buffers
ser.flushInput()
ser.flushOutput()

time.sleep(.1)

settime()       #Set the time
readnprint()

print("INFO: Starting main loop...")

while True:
    bat = psutil.sensors_battery()                                      #Update battery status
    if (bat.power_plugged == False) and (rec_off == False):             #If we lost mains power and the recorder is on...
        print("ALERT: On battery, beginning countdown")
        for i in range(0, 300):                                         #Start a 300sec (5min) countdown
            bat = psutil.sensors_battery()                              #Update battery status
            if bat.power_plugged == True:                               #If mains are restored, halt the countdown and back out of this loop
                print("INFO: Mains restored, countdown halted")
                break
            time.sleep(1)
        bat = psutil.sensors_battery()                                  #Update battery status
        if bat.power_plugged == False:                                  #If we still don't have mains after 5min...
            print("ALERT: Countdown elapsed, powering off recorder")
            ser.flushInput()                                            #Flush the input buffer
            time.sleep(.1)
            ser.write(stop)                                             #Stop and active recording
            readnprint()
            ser.write(off)                                              #Turn off the recorder
            readnprint()
            rec_off = True
    elif bat.power_plugged and rec_off:                                 #If power is back on and the recorder isn't...
        ser.flushInput()                                                #Flush the input buffer
        time.sleep(.1)
        ser.write(on)                                                   #Turn the recorder on
        readnprint()
        rec_off = False                                                 #Remember that we turned it back on
        print("INFO: Mains restored, powering on recorder")
    if time_count == (60*60*24*7):                                      #If it's been a week, sync the time
        settime()
        time_count = 0
    else:
        time_count = time_count + 1
    time.sleep(1)                                                       #Run through all that ^^^ every second
            

ser.close()

