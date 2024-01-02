import time
from machine import Pin
import network
import ntptime
import urequests as requests
import ujson

station_id = 0
url = ''
myobj = {'email': '', 'password': ''}
url_send = '' + str(station_id)

pin_number = 22
period = 10 # minutes, int only for now
ssid = ''
password = ''

# set led pin
led = Pin(2, Pin.OUT)
# blink 3 times, 0.5 seconds each
i = 0
while i < 3:
    led.on()
    time.sleep(0.5)
    led.off()
    time.sleep(0.5)
    i = i + 1

tippings = 0

# print start
print('Starting program')
print(f'Period: {period} minutes')

elapsed_time = time.time_ns()

def callback(pin):
    global tippings
    global elapsed_time
    current_time = time.time_ns()
    difference = current_time - elapsed_time
    difference = round(difference/1000000000,2)
    if difference < 0.1:
        print('Too fast, not counting')
        return
    elapsed_time = current_time
    tippings = tippings + 1
    print(f'Tip number {tippings}, difference between last tip: {difference}')

p = Pin(pin_number, Pin.IN)
p.irq(trigger=Pin.IRQ_RISING, handler=callback)

# connect to wifi
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
while not sta_if.isconnected():
    print('Connecting to network...')
    sta_if.connect(ssid, password)


# get time from server
ntptime.settime()

# get time
now = time.localtime()
min = now[4]
sec = now[5]

# set alarm
alarm = time.time() + (((min//period)*period + period) - min)*60 - (60 - sec) + 5

# main loop
print('Starting main loop')
while True:
    if time.time() > alarm:
        print('Sending data to server')
        sta_if.connect(ssid, password)
        now = time.localtime()
        time_stamp = f'{now[0]:04}-{now[1]:02}-{now[2]:02} {now[3]:02}:{(now[4]//period)*period:02}:00'
        min = now[4]
        sec = now[5]
        # convert data
        if tippings == 0:
            volume = 0
        else:
            volume = (-2.35/(0.05-(166.667/tippings))/6)*1000
            volume = round(volume, 2)
        tippings = 0
        i = 0
        while i < 5:
            try:
                print(f'Volume: {volume} ml in {period} minutes')
                # get parameters
                x = requests.post(url, headers = {'content-type': 'application/json'}, data = ujson.dumps(myobj))
                time.sleep(0.1)
                token = dict(x.json()).get('access_token')
                # send data
                header = {'Authorization': f'Bearer {token}', 'content-type': 'application/json'}
                my_dict = [{"station_id": station_id, "date": time_stamp, "s1": volume}]
                json_object = ujson.dumps(my_dict)
                x = requests.get(url_send, data = json_object, headers = header)
                print(x.text)
                time.sleep(0.1)
                i = 5
            except:
                i = i+1
                print('Error sending data')
        alarm = time.time() + (((min//period)*period + period) - min)*60 - (60 - sec) + 5
