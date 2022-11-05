import network
import WIFI_CONFIG
import socket
import time
from random import random, uniform, randint

from machine import Pin
import uasyncio as asyncio

import plasma
from plasma import plasma_stick

onboard = Pin("LED", Pin.OUT, value=0)

onboard.on()
time.sleep(0.1)
onboard.off()
time.sleep(0.5)
onboard.on()

# Set how many LEDs you have
NUM_LEDS = 50

# set up the WS2812 / NeoPixel™ LEDs
led_strip = plasma.WS2812(NUM_LEDS, 0, 0, plasma_stick.DAT, color_order=plasma.COLOR_ORDER_RGB)

# start updating the LED strip
led_strip.start()

mode = "Off"

html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RPi Pico Wireless Plasma Kit</title>
    </head>
    <body>
    <div align="center">
    <H1>RPi Pico Wireless Plasma Kit</H1>
    <h2>State: <strong>%s</strong></h2>
    <p>
    <a href="/?mode=Blinky"><button class="button">Blinky</button></a> 
    <a href="/?mode=Fire"><button class="button">Fire</button></a> 
    <a href="/?mode=Rainbows"><button class="button">Rainbows</button></a> 
    <a href="/?mode=Spooky"><button class="button">Spooky</button></a> 
    <a href="/?mode=Off"><button class="button">Off</button></a>
    </p>
    </div>
    </body>
    </html>
    """

def known_ap(aps):
    print("Checking for known AP...") 
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    time.sleep(1)
    found_aps = wlan.scan()
    wlan.deinit()
    print(found_aps)
    for ap in aps:
        print(ap)
        for fap in found_aps:
            if ap[0] in fap[0]:
                return ap
    return None

def connect_to_network(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.config(pm = 0xa11140) # Disable power-save mode
    wlan.connect(ssid, password)

    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        time.sleep(1)

    if wlan.status() != 3:
        raise RuntimeError(f'network connection failed: {wlan.status()}')
    else:
        print('connected')
        status = wlan.ifconfig()
        print('ip = ' + status[0])

def setup_ap(essid="Pico-AP", password="12345678"):
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=essid, password=password)
    ap.active(True)

    while ap.active() == False:
      pass

    print('AP successfully created')
    print(f"Essid: {essid}  Password: {password}")
    print(ap.ifconfig())

    #print('ip = ' + status[0])

async def serve_client(reader, writer):
    global mode
    print("Client connected")
    request_line = await reader.readline()
    print("Request:", request_line)
    # We are not interested in HTTP request headers, skip them
    while await reader.readline() != b"\r\n":
        pass

    request = str(request_line)
    cmd = request.find("/?mode=")
    if cmd > 0:
        mode2 = request.find(" HTTP/1.1")
        cmd = request[cmd+7:mode2]
        mode = cmd
        print(f"-mode: {mode}")
    else:
        cmd = "UnKnown"

    response = html % cmd
    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    writer.write(response)

    await writer.drain()
    await writer.wait_closed()
    print("Client disconnected")

async def main():
    ap = known_ap(WIFI_CONFIG.APs)
    if ap:
        print('Connecting to Network...')
        connect_to_network(ap[0], ap[1])
    else:
        print("Setting up Access Point...")
        setup_ap("Skull-AP")

    print('Setting up webserver...')
    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 80))

    while True:
        #print(mode, end=' ')
        if mode == "Off":
            print("Off!")
            for i in range(NUM_LEDS):
                led_strip.set_rgb(i, 0, 0, 0)
            while mode == "Off":
                onboard.on()
                await asyncio.sleep(0.1)
                onboard.off()
                await asyncio.sleep(0.9)

        elif mode == "Blinky":
            print("Blinky!")
            # Pick two hues from the colour wheel (from 0-360°, try https://www.cssscript.com/demo/hsv-hsl-color-wheel-picker-reinvented/ )
            #HUE_1 = 40
            #HUE_2 = 285
            HUE_1 = randint(0, 179)
            HUE_2 = randint(180, 359)
            print(f"Hue1: {HUE_1}  Hue2: {HUE_2}")
            # Set up brightness (between 0 and 1)
            BRIGHTNESS = 0.5
            # Set up speed (wait time between colour changes, in seconds)
            SPEED = 1

            while mode == "Blinky":
                for i in range(NUM_LEDS):
                    # the if statements below use a modulo operation to identify the even and odd numbered LEDs
                    if (i % 2) == 0:
                        led_strip.set_hsv(i, HUE_1 / 360, 1.0, BRIGHTNESS)
                    else:
                        led_strip.set_hsv(i, HUE_2 / 360, 1.0, BRIGHTNESS)
                await asyncio.sleep(SPEED)

                for i in range(NUM_LEDS):
                    if (i % 2) == 0:
                        led_strip.set_hsv(i, HUE_2 / 360, 1.0, BRIGHTNESS)
                    else:
                        led_strip.set_hsv(i, HUE_1 / 360, 1.0, BRIGHTNESS)
                await asyncio.sleep(SPEED)

        elif mode == "Fire":
            print("Fire!")
            while mode == "Fire":
                # fire effect! Random red/orange hue, full saturation, random brightness
                for i in range(NUM_LEDS):
                    led_strip.set_hsv(i, uniform(0.0, 50 / 360), 1.0, random())
                await asyncio.sleep(0.1)

        elif mode == "Rainbows":
            print("Rainbows!")
            BRIGHTNESS = 0.5 # Set up brightness (between 0 and 1)
            SPEED = 20 # The SPEED that the LEDs cycle at (1 - 255)
            UPDATES = 60 # How many times the LEDs will be updated per second
            offset = 0.0

            while mode == "Rainbows":
                offset += float(SPEED) / 2000.0
                for i in range(NUM_LEDS):
                    hue = float(i) / NUM_LEDS
                    led_strip.set_hsv(i, hue + offset, 1.0, BRIGHTNESS)
                await asyncio.sleep(1.0 / UPDATES)

        elif mode == "Spooky":
            print("Spooky!")
            HUE_START = 30  # orange
            HUE_END = 140  # green
            BRIGHTNESS = 0.5 # Set up brightness (between 0 and 1)
            SPEED = 0.3  # bigger = faster (harder, stronger)
            distance = 0.0
            direction = SPEED

            while mode == "Spooky":
                for i in range(NUM_LEDS):
                    # generate a triangle wave that moves up and down the LEDs
                    j = max(0, 1 - abs(distance - i) / (NUM_LEDS / 3))
                    hue = HUE_START + j * (HUE_END - HUE_START)

                    led_strip.set_hsv(i, hue / 360, 1.0, BRIGHTNESS)

                # reverse direction at the end of colour segment to avoid an abrupt change
                distance += direction
                if distance > NUM_LEDS:
                    direction = - SPEED
                if distance < 0:
                    direction = SPEED
                await asyncio.sleep(0.01)

        else:
            print("Unknown!")
            await asyncio.sleep(2)

try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()
