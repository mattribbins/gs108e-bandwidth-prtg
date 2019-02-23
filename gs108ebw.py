# Netgear ProSAFE GS1xxE Bandwith PRTG Monitor
#
# Version: 1.1
# Author: Matt Ribbins (mattyribbo.co.uk)
# Description: PRTG script that scrapes the traffic data from a Netgear ProSAFE Web Managed (Plus) switch
# Dependencies: python3, requests, paepy (bundled with PRTG)
# Usage: ./gs108ebw.py -i <ip address> -p <password> -n <port number>

import time, sys, getopt, tempfile, json
import requests, requests.cookies
from paepy.ChannelDefinition import CustomSensorResult
from lxml import html

# Script Defaults
sleep_time = 0.25  # How long to wait between sending requests to the switch
cookie_dir = tempfile.gettempdir() # Where to store script files. Default OS temp dir


# Custom Sensor class
# This takes the CustomSensorResult class from paepy and adds additional functionality that is needed.
class AdvancedCustomSensorResult(CustomSensorResult):
    def add_channel(
            self,
            channel_name,
            is_limit_mode=False,
            limit_max_error=None,
            limit_max_warning=None,
            limit_min_error=None,
            limit_min_warning=None,
            limit_error_msg=None,
            limit_warning_msg=None,
            decimal_mode=None,
            mode=None,
            value=None,
            unit='Custom',
            speed_size=None,
            speed_time=None,
            is_float=False,
            value_lookup=None,
            show_chart=True,
            warning=False,
            primary_channel=False
    ):
        channel = {}

        # Process in parent class
        super(AdvancedCustomSensorResult, self).add_channel(channel_name, is_limit_mode, limit_max_error,
                                                            limit_max_warning, limit_min_error, limit_min_warning,
                                                            limit_error_msg, limit_warning_msg,
                                                            decimal_mode, mode, value, unit, is_float, value_lookup,
                                                            show_chart, warning, primary_channel)

        # Get the channel from the original class
        if primary_channel:
            channel = self.channels[0]
        else:
            channel = self.channels[len(self.channels) - 1]

        # Additional functionality

        if speed_size is not None and self.__is_valid_size(speed_size):
            channel['SpeedSize'] = speed_size

        if speed_time is not None and self.__is_valid_time(speed_time):
            channel['SpeedTime'] = speed_time

        if is_limit_mode:
            channel['LimitMode'] = 1
            if limit_max_error is not None:
                channel['LimitMaxError'] = limit_max_error
            if limit_max_warning is not None:
                channel['LimitMaxWarning'] = limit_max_warning
            if limit_min_error is not None:
                channel['LimitMinError'] = limit_min_error
            if limit_min_warning is not None:
                channel['LimitMinWarning'] = limit_min_warning
            if limit_error_msg is not None:
                channel['LimitErrorMsg'] = limit_error_msg
            if limit_warning_msg is not None:
                channel['LimitWarningMsg'] = limit_warning_msg

        # Re-save
        if primary_channel:
            self.channels[0] = channel
        else:
            self.channels[len(self.channels) - 1] = channel

    @staticmethod
    def __is_valid_size(unit):

        valid_size = {
            "One",
            "Kilo",
            "Mega",
            "Giga",
            "Tera",
            "Byte",
            "KiloByte",
            "MegaByte",
            "GigaByte",
            "TeraByte",
            "Bit",
            "KiloBit",
            "MegaBit",
            "GigaBit",
            "TeraBit"
        }

        if unit not in valid_size:
            return True
        else:
            return False

    @staticmethod
    def __is_valid_time(time):

        valid_time = {
            "Second"
            "Minute"
            "Hour"
            "Day"
        }

        if time not in valid_time:
            return True
        else:
            return False


# ## Functions ## #


# Get login cookie
# Parameters: (string) Switch IP, (strong) Switch Password
# Return: (string) Cookie name, (string) Cookie content
def get_login_cookie(switch_ip, switch_password):
    # Login through the web interface and retrieve a session key
    url = 'http://' + switch_ip + '/login.cgi'
    data = dict(password=switch_password)

    r = requests.post(url, data=data, allow_redirects=True)

    # Check that we have authenticated correctly. Cookie must be set
    cookie = r.cookies.get('GS108SID')
    if cookie is not None:
        return 'GS108SID', cookie

    cookie = r.cookies.get('SID')
    if cookie is not None:
        return 'SID', cookie

    # If we've got here, then authentication error or cannot find the auth cookie.
    return (None), (None)


# Check if cookie is valid
# Parameters: (string) Switch IP, (string) Cookie name, (string) Cookie contents
# Return: True or False
def check_login_cookie_valid(switch_ip, cookie_name, cookie_content):
    # Checks that our login cookie is indeed valid. We check the port stats page, if that page loads correctly, (y).
    # Return: bool
    url = 'http://' + switch_ip + '/portStatistics.cgi'
    jar = requests.cookies.RequestsCookieJar()
    jar.set(cookie_name, cookie_content, domain=switch_ip, path='/')
    r = requests.post(url, cookies=jar, allow_redirects=False)
    tree = html.fromstring(r.content)
    title = tree.xpath('//title')
    if title[0].text != "Port Statistics":
        return False
    else:
        return True


# Here we go...
def main(argv):
    is_new_cookie = False
    switch_ip = "192.168.0.2"
    switch_password = "notSetOne"
    switch_cookie = ""
    port_number = 0

    # Get PRTG parameters
    try:
        # Load from PRTG JSON
        prtg = json.loads(argv[0])
        params = str.split(prtg['params'])

        # Decode the arguments
        opts, args = getopt.getopt(params, "hi:p:n:", ["port=", "ip=", "password=",])
        for opt, arg in opts:
            if opt == '-h':
                result = CustomSensorResult()
                result.add_error(("No arguments found."))
                exit()
            # Port number
            elif opt in ("-n", "--port"):
                port_number = int(arg)
                # We assume port given is human, not binary. Just in case
                if port_number > 0:
                    port_number -= 1
            elif opt in ("-p", "--password"):
                switch_password = str(arg)
            elif opt in ("-i", "--ip"):
                switch_ip = str(arg)
    except json.JSONDecodeError as err:
        result = CustomSensorResult()
        result.add_error(("No arguments provided." + err.msg))
        print(result.get_json_result())
        exit(1)
    except getopt.GetoptError as err:
        result = CustomSensorResult()
        result.add_error(("Incorrect syntax." + err.msg))
        exit(2)

    # Check if we have a stored cookie file
    try:
        f = open(cookie_dir + '/.gs108ecookie' + switch_ip, 'r')
        switch_cookie_name = f.readline().rstrip('\n')
        switch_cookie_content = f.readline().rstrip('\n')
        f.close()
        if check_login_cookie_valid(switch_ip, switch_cookie_name, switch_cookie_content) is False:
            raise IOError
    except IOError:
        # File doesn't exist. Get login key
        is_new_cookie = True
        switch_cookie_name, switch_cookie_content = get_login_cookie(switch_ip, switch_password)
        if switch_cookie_name is None:
            result = CustomSensorResult()
            result.add_error(("Cookie jar is empty. Dir:" + cookie_dir))
            print(result.get_json_result())
            exit(1)
        f = open(cookie_dir + '/.gs108ecookie' + switch_ip, 'w')
        f.write(switch_cookie_name + "\n")
        f.write(switch_cookie_content + "\n")
        f.write(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
        f.close()

    # Set up our cookie jar
    jar = requests.cookies.RequestsCookieJar()
    jar.set(switch_cookie_name, switch_cookie_content, domain=switch_ip, path='/')

    # Get the port stats page
    url = 'http://' + switch_ip + '/portStatistics.cgi'
    page = requests.get(url, cookies=jar)
    start_time = time.perf_counter()
    tree = html.fromstring(page.content)

    # Scrape the data
    if(switch_cookie_name == "SID"):
        # GS105Ev2 format (no element names!)
        rx1 = tree.xpath('//tr[@class="portID"]//input[@type="hidden"][2]')
        tx1 = tree.xpath('//tr[@class="portID"]/input[@type="hidden"][4]')
        crc1 = tree.xpath('//tr[@class="portID"]/input[@type="hidden"][6]')
    else:
        # GS108Ev3 format
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
    if(switch_cookie_name == "SID"):
        # GS105Ev2 format (no element names!)
        rx2 = tree.xpath('//tr[@class="portID"]//input[@type="hidden"][2]')
        tx2 = tree.xpath('//tr[@class="portID"]/input[@type="hidden"][4]')
        crc2 = tree.xpath('//tr[@class="portID"]/input[@type="hidden"][6]')
    else:
        # GS108Ev3 format
        rx2 = tree.xpath('//tr[@class="portID"]/input[@name="rxPkt"]')
        tx2 = tree.xpath('//tr[@class="portID"]/input[@name="txpkt"]')
        crc2 = tree.xpath('//tr[@class="portID"]/input[@name="crcPkt"]')

    sample_time = end_time - start_time
    sample_factor = 1 / sample_time

    # print("It took us " + str(sample_time) + " seconds.")

    # Test code, print all values.
    # for i in range(0, len(tx2)):
    #    # Convert Hex to Int, get bytes traffic
    #    port_traffic = int(tx2[i].value, 16) - int(tx1[i].value, 16)
    #    port_speed_bps = port_traffic * sample_factor
    #    print("Port " + str(i) + ": " + "{0:.2f}".format(port_speed_bps/1024, ) + "kbps.")


    if(switch_cookie_name == "SID"):
        # GS105Ev2
        # Values are already in Int
        port_traffic_rx = int(rx2[port_number].value, 10) - int(rx1[port_number].value, 10)
        port_traffic_tx = int(tx2[port_number].value, 10) - int(tx1[port_number].value, 10)
        port_traffic_crc_err = int(crc2[port_number].value, 10) - int(crc2[port_number].value, 10)
        port_speed_bps_rx = port_traffic_rx * sample_factor
        port_speed_bps_tx = port_traffic_tx * sample_factor
        port_name = "Port " + str(port_number)
    else:
        # GS108Ev3 format
        # Convert Hex to Int, get bytes traffic
        port_traffic_rx = int(rx2[port_number].value, 16) - int(rx1[port_number].value, 16)
        port_traffic_tx = int(tx2[port_number].value, 16) - int(tx1[port_number].value, 16)
        port_traffic_crc_err = int(crc2[port_number].value, 16) - int(crc2[port_number].value, 16)
        port_speed_bps_rx = port_traffic_rx * sample_factor
        port_speed_bps_tx = port_traffic_tx * sample_factor
        port_name = "Port " + str(port_number)

    # Use paepy to form a meaningful response for PRTG.
    result = AdvancedCustomSensorResult()

    result.add_channel("Traffic In", unit="BytesBandwidth", value=port_speed_bps_rx, is_float=False,
                       speed_size="KiloBytes")
    result.add_channel("Traffic Out", unit="BytesBandwidth", value=port_speed_bps_tx, is_float=False,
                       speed_size="KiloBytes")
    result.add_channel("CRC Errors", unit="CRC Errors", value=port_traffic_crc_err)
    result.add_channel("Response Time", unit="TimeResponse", value=sample_time * 1000, is_float=True)

    # Print the result
    print(result.get_json_result())


# Fin
if __name__ == "__main__":
    main(sys.argv[1:])
