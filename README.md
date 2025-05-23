
## The Growatt Inverter Monitor nu-grott
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/donate/?hosted_button_id=7X7GKFKESAH6G)

nu-grott is a software to free growatt inverters from using the manufacturers cloud service. 


### Feature List

* collect data from one or several growatt inverters
* convert the data to your personal needs
* provide the collected data to other applications
* integration with HomeAssistant
* data forwarding via MQTT
* data storage in a local database
* data forwarding to PVOutput website
* parameter readout from the inverter
* parameter setting into the inverter
* simulation of smart meter data retrieved from other sensors


### Reason for this fork

The nu-grott project is a fork of the [grott](https://github.com/johanmeijer/grott) project.

It was necessary to start this fork, as grott's author refuses code improvements 
and modifications to his project. To differentiate the fork from it's origin 
the name has been changed to nu-grott. 

nu-grott aims to keep the functionality from grott but adds improvements and new features.

In contrast to the original code nu-grott
* focuses on code quality
* uses self-expanatory code and has fully and correctly documented source code
* is fully written in english language 
* accepts improvements and additions from contributors (see doc/CONTRIBUTING.md) 
* has full test coverage to avoid regression errors 
* allows adding new features easily
* may not be backward compatible to the original grott
* pays attention for security risks and actively avoids them


### Should I switch from grott to nu-grott

* If you never used grott before you can savely start with nu-grott.
* If you are running grott and you are happy with it, keep it running.
* If you are running grott and experiance problems or miss features, that you 
might swich to new grott. It might happen that you need to adjust your existing 
grott.ini as I do not garantee backward compatibility. The changes should be
simple though. 
* nu-grott is not tested with all Growatt devices yet. I welcome everyone to
try nu-grott and if there are any issues are happy to fix them to make nu-grott
suitable for all Growatt users. 


### One mode of operation
nu-grott intercepts the inverter communication, processes it and keeps the
communication with the growatt server
* Proxy mode (man in the middle): The Growatt ShineWifi or ShineLAN box can be easily configured to use nu-grott as an alternative server to the default server.growatt.com. Grott then acts as a relay to the Growatt servers. nu-grott reads the transmitted data and then forwards the data to server.growatt.com.


### Where nu-grott can forward data to
nu-grott can forward the parsed metrics to: 
* Home Assistant
* MQTT (suggested option for many home automation systems such as Home Assistant, OpenHAB and Domoticz)
* Database InfluxDB v1 and v2 (a time series database with dashboarding functionality) 
* PVOutput.org (a service for sharing and comparing PV output data)
* Custom output using the extension functionality (Examples available for Export to CSV files and writing to a Http Server).


### Compatibility
The program is written in python and runs under any operation system that
provides a python3 interpreter. It was tested on windows, linux, mac but may
run on other systems as well.

It can run:
* Interactive from the command line interface
* As a Linux or Windows service
* As a [Docker container](https://github.com/stefan-nu/grott/wiki/Docker-support).  

The Docker images are tested on Raspberry Pi(arm32), Ubuntu and Synology NAS


### Supported Growatt Inverters

nu-grott was tested, but not limited to, these growatt inverter models:

+ 1500-S (ShineWiFi)
+ 3000-S  (Shinelan)
+ 2500-MTL-S (ShineWiFi)
+ 4200-MTL-S (Shinelan)
+ 5000TL-X   (ShineWifi-X)
+ 3600TL-XE (ShineLink-X)
+ 3600TL-XE (ShineLan)
+ MOD 5000TL3-X* (ShineLan)
+ MOD 9000TL3-X*


## Installing nu-grott

### ShineLAN or ShineWIFI configuration

The Growatt datalogger (ShineLAN box or ShineWIFI) [needs to be configured](https://github.com/stefan-nu/grott/wiki/Rerouting-Growatt-Wifi-TCPIP-data-via-your-Grott-Server) to send data to nu-grott instead of the Growatt server API.
Please see the [Wiki](https://github.com/stefan-nu/grott/wiki) for further information and installation details. 


nu-grott is listening on an TCP port (default 5279), processes the data and forwards the original packet to the growatt server. 

The proxy mode functionality can be enabled by: 

- mode = proxy in the conf.ini file 
- m proxy parameter during startup


## No Liability

nu-grott is provided as is without any garantee or liability. 
You may use it free of charage at your own risk.


## Smart Meter Replacement

If you do not use a smart meter yet, nu-grott can also acquire meter values
from other enery counters and provide those to the growatt device. Thus nu-grott
can simulate a smart meter. I do not provide this feature on the nu-grott version
on github. If you consider a donation, you can get this additional feature which
will safe you 100 Euros plus the installation cost for a smart meter.


## Custom Feature request

If you need a special feature that is not present on nu-grott currently, please
open an Issue. If I consider the feature useful and feasable for all users I 
will implement it. If it is something you need urgently please contact me.


## Coding support

I work as a software developer for many years now. I am specialized in low
level C/C++ programming mainly for embedded devices. 

If you need professional developent suport don't hesitat to get in touch with me.

nu-grott is written in Python because the original project grott was in Python. As I am no Python specialist, I might port it to C at some point. 
You can see from the source code, that Python is suitable to do such projects.
However C or C++ would be much more efficient and I would like it more, too.
Anyway as a programmer I am able to work in any programming language.

To judge my coding skills, please compare nu-grott to the original grott code. 
If you like my version better, consider to get in touch, otherwise not. 


## Donations

Donations help to further improve this software.
If you need a specific modification or feature, please contact the project owner.



[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/donate/?hosted_button_id=7X7GKFKESAH6G)
