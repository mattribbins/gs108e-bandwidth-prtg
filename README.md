# GS108E Bandwidth Sensor for PRTG (gs108ebw.py)

This PRTG python script provides a custom sensor for PRTG, allowing you to monitor traffic consumption on your Netgear GS108E switch (and other related models).

This script came into existance as the web interface only provided traffic counters and no current traffic loads. There is no SNMP functionality on the switch either. A custom sensor is required to be able to display this information on PRTG.

### Requirements

gs108ebw requires a few dependencies:

* [PRTG] - Obvious!
* [lxml] - Python XML and HTML parser
* [requests] - Python HTTP request library. Miles easier to use than urllib!

### Screenshots

When a sensor is configured, you will get the following information in PRTG.
![GS108E sensor displaying all available channels](https://mattyribbo.co.uk/wp-content/uploads/2017/02/Screen-Shot-2017-02-07-at-21.09.15.png)


### Installation

It is strongly recommended that you install pip on the PRTG python installation (if you haven't already). A reduction in headaches is always positive!

Download the [get-pip.py](https://bootstrap.pypa.io/get-pip.py) script and save it to the PRTG Python folder. Open a command prompt on yo with Administrator rights on your PRTG server and run the script. Adjust the directory as appropriate.
```
C:\Program Files (x86)\PRTG Network Monitor\Python34\python.exe get-pip.py
```

Once pip is installed successfully, you can now run pip to install requests
```
C:\Program Files (x86)\PRTG Network Monitor\Python34\Scripts\pip.exe install requests
```

Installing lxml is done differently. Download the unofficial precompiled lxml package from [Christoph Gohlke](http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml). (Should you wish to compile and install lxml instead then feel free, though expect headaches galore!)
```
C:\Program Files (x86)\PRTG Network Monitor\Python34\Scripts\pip.exe install lxml-3.7.2-cp34-cp34m-win32.whl
```
\* You can install lxml through pip, but you then need to build and compile libxml and have all the compiler paths set correctly. At your own risk.

The final step is to copy the gs108ebw.py script to the PRTG custom sensors folder, and edit the settings to match your environment (IP address and password)
```
C:\Program Files (x86)\PRTG Network Monitor\Custom Sensors\python
```
### Usage
Once the script is installed on the PRTG server, open up the web console and navigate to the device where you want to log traffic.

### Limitations

- It's slow! The web interface isn't the fastest thing in the world.
- Errors can occur when running the script via PRTG. Debugging via PRTG isn't great.
- False positives can occur. Negatives or completely unreasonable "spikes" can appear. You can set up your PRTG sensor to counter those issues, but work will be done to build some of that functionality in.

### Todos
 - Caching data to reduce the amount of calls made to the switch.
 - More command line parameters instead of hard coded values.
 - Built in functionality to ignore false values.
 - Remove the global variable nightmare!
 - Code clean-up. Perhaps make it into a class...

### License
BSD 2-Clause Licence

### Help!
There is the possibility that you will come across the occasional warning where the script has timed out or thrown an error. Increasing the sensor interval time and/or the sleep interval in the script may alleviate the issue. Caching data is on the to-do list which will help further.

If you're still stuck then please raise an issue on GitHub.

[//]: #


   [PRTG]: <https://www.paessler.com/prtg>
   [git-repo-url]: <https://github.com/joemccann/dillinger.git>
   [PRTG]: <https://www.paessler.com/prtg>
   [lxml]: <http://lxml.de>
   [requests]: <http://docs.python-requests.org/en/master/>
