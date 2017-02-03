# GS108E Bandwith PRTG Monitor
#
# Author: Matt Ribbins (mattyribbo.co.uk)
# Description: PRTG script that scrapes the traffic data from a Netgear Web Managed (Plus) GS108E switch
# Dependencies: python3, requests, paepy (bundled with PRTG)

import time, sys, getopt
import requests, requests.cookies
from paepy.ChannelDefinition import CustomSensorResult
from lxml import html


### Settings ###
switch_ip = '192.168.0.2'
switch_password = 'changeME'

### Defaults ###
port_number = 0     # If no arguments, what port to check?
sleep_time = 0.25   # How long to wait between sending requests to the switch
cookie_dir = "~"    # Where to store cookie file

### Variables ###
switch_cookie = ''


### Functions ###
def get_login_cookie():
    # Login through the web interface and retrieve a session key
    url = 'http://' + switch_ip + '/login.cgi'
    data = dict(password=switch_password)

    r = requests.post(url, data=data, allow_redirects=True)

    cookie = r.cookies.get('GS108SID')

    # Check that we have authenticated correcty. GS108SID cookie must be set
    if cookie is None:
        return(None)
    else:
        return cookie

def check_login_cookie_valid():
    # Checks that our login cookie is indeed valid. We check the port stats page, if that page loads correctly, (y).
    # Return: bool
    url = 'http://' + switch_ip + '/port_statistics.htm'
    jar = requests.cookies.RequestsCookieJar()
    jar.set('GS108SID', switch_cookie, domain=switch_ip, path='/')
    r = requests.post(url, cookies=jar, allow_redirects=False)
    tree = html.fromstring(r.content)
    title = tree.xpath('//title')
    if title[0].text != "Port Statistics":
        return False
    else:
        return True;

### Here we go... ###

def usage():
    #print(argv[0] + ' -p <port_number>')
    result = CustomSensorResult()
    result.add_error(("Incorrect syntax. Requires arguments: -p <port_number>"))

def main(argv):
    # Get command args
    try:
        opts, args = getopt.getopt(argv,"hp:",["port="])
    except getopt.GetoptError as err:
        print(err)
        usage()
        exit(1)
    for opt, arg in opts:
        if opt == '-h':
            usage()
            exit()
        # Port number
        elif opt in ("-p", "--port"):
            port_number = int(arg)
            # We assume port given is human, not binary. Just in case
            if port_number > 0:
                port_number -= 1

    # Check if we have a stored cookie file
    try:
        f = open('gs108e.cookie', 'r')
        switch_cookie = f.read()
        f.close()
        if check_login_cookie_valid() is False:
            raise IOError
    except IOError:
        # File doesn't exist. Get login key
        switch_cookie = get_login_cookie()
        if switch_cookie is None:
            result = CustomSensorResult()
            result.add_error(("Cookie jar is empty."))
        f = open('gs108e.cookie', 'w')
        f.write(switch_cookie)
        f.close()

    # Set up our cookie jar
    jar = requests.cookies.RequestsCookieJar()
    jar.set('GS108SID', switch_cookie, domain=switch_ip, path='/')

    # Get the port stats page
    url = 'http://' + switch_ip + '/port_statistics.htm'
    page = requests.get(url, cookies=jar)
    start_time = time.perf_counter()
    tree = html.fromstring(page.content)

    # Scrape the data
    rx1 = tree.xpath('//tr[@class="portID"]/input[@name="rxPkt"]')
    tx1 = tree.xpath('//tr[@class="portID"]/input[@name="txpkt"]')
    crc1 = tree.xpath('//tr[@class="portID"]/input[@name="crcPkt"]')

    # Hold fire
    time.sleep(sleep_time)

    # Get the port stats page again! We need to compare two points in time
    page = requests.get(url, cookies=jar)
    end_time = time.perf_counter()
    tree = html.fromstring(page.content)

    # Scrape the data
    rx2 = tree.xpath('//tr[@class="portID"]/input[@name="rxPkt"]')
    tx2 = tree.xpath('//tr[@class="portID"]/input[@name="txpkt"]')
    crc2 = tree.xpath('//tr[@class="portID"]/input[@name="crcPkt"]')

    sample_time = end_time - start_time
    sample_factor = 1 / sample_time
    print("It took us " + str(sample_time) + " seconds.")

    # Test code, print all values.
    #for i in range(0, len(tx2)):
    #    # Convert Hex to Int, get bytes traffic
    #    port_traffic = int(tx2[i].value, 16) - int(tx1[i].value, 16)
    #    port_speed_bps = port_traffic * sample_factor
    #    print("Port " + str(i) + ": " + "{0:.2f}".format(port_speed_bps/1024, ) + "kbps.")


    # Convert Hex to Int, get bytes traffic
    port_traffic_rx = int(rx2[port_number].value, 16) - int(rx1[port_number].value, 16)
    port_traffic_tx = int(tx2[port_number].value, 16) - int(tx1[port_number].value, 16)
    port_traffic_crc_err = int(crc2[port_number].value, 16) - int(crc2[port_number].value, 16)
    port_speed_bps_rx = port_traffic_rx * sample_factor
    port_speed_bps_tx = port_traffic_tx * sample_factor
    port_name = "Port " + str(port_number)

    # Use paepy to form a meaningful response for PRTG.
    result = CustomSensorResult()

    result.add_channel("Traffic In", unit="SpeedNet", value=port_speed_bps_rx)
    result.add_channel("Traffic Out", unit="SpeedNet", value=port_speed_bps_tx)
    result.add_channel("CRC Errors", unit="CRC Errors", value=port_traffic_crc_err)

    # Print the result
    print(result.get_json_result())

# Fin
if __name__ == "__main__":
   main(sys.argv[1:])