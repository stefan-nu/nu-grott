
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

The nu-grott project is a fork of the original [grott](https://github.com/johanmeijer/grott) project.

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


### Two modes of metric data retrieval
Grott can intercept the inverter metrics in two distinct modes:
* Proxy mode (man in the middle): The Growatt ShineWifi or ShineLAN box can be easily configured to use Grott as an alternative server to the default server.growatt.com. Grott then acts as a relay to the Growatt servers. Grott reads the transmitted data, and then forwards the data to server.grott.com.
* Sniff mode (original connection): Can be used if your router is linux based. IPTables NAT masquerading is used in conjuction with a python packet sniffer to read the data. (This is more resource intensive on the linux host).


### Where Grott can forward metric data to
Grott can forward the parsed metrics to: 
* MQTT (suggested option for many home automation systems such as Home Assistant, OpenHAB and Domoticz)
* InfluxDB v1 and v2 (a time series database with dashboarding functionality) 
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


## Grott installation

### ShineLAN or ShineWIFI configuration

If Grott is running in proxy mode the ShineLAN box or ShineWIFI module [needs to be configured](https://github.com/stefan-nu/grott/wiki/Rerouting-Growatt-Wifi-TCPIP-data-via-your-Grott-Server) to send data to Grott instead of the Growatt server API.
Please see the [Wiki](https://github.com/stefan-nu/grott/wiki) for further information and installation details. 


With the proxy mode Grott is listening on an IP port (default 5279), processes the data (sent MQTT message) and routes the original packet to the growatt website. 

The proxy mode functionality can be enabled by: 

- mode = proxy in the conf.ini file 
- m proxy parameter during startup

Pro / Cons: 

    sniff mode
    + Data will also be routed to the growatt server if Grott is not active
    - All TCP packages (also not growatt) need to be processed by Grott. 
      This is more resource (processor) intesive and can have a negative impact on the device performance.
    - Configure IP forwarding can be complex if a lot of other network routing is configured (e.g. by Docker). 
    - Sudo rights necessary to allow network sniffering
    
    proxy mode: 
    + Simple configuration 
    + Only Growatt IP records are being analysed and processed by Grott 
    + Less resource intensive 
    + No sudo rights needed
    + Blocking / Filtering of commands from the outside is possible
    - If Grott is not running no data will be sent to the Growatt server

The adivse is to use the proxy mode. This mode is strategic and will be used for enhanced features like automatic protocol detection and command blocking filtering.  
<br>
Sniff mode is not supported under Windows
<br>
In sniff mode it is necessary to run nu-grott with sudo rights. 

## No Liability

nu-grott is provided as is without any garantee or liability. 
You may use it free of charage at your own risk.

## Donations

Donations help to further improve this software.
If you need a specific modification or feature, please contact the project owner.

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/donate/?hosted_button_id=7X7GKFKESAH6G)
