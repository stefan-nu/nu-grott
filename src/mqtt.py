#import mqtt
import paho.mqtt.publish as publish


def mqtt_processing(conf, header, jsonmsg, deviceid):
    
    # if meter data use mqtttopicname topic
    record_type = header[14:16]
    if (record_type in ("20", "1b")) and (conf.mqttmtopic == True) :
        mqtttopic = conf.mqttmtopicname
    else :
        # test if invertid needs to be added to topic
        if conf.mqttinverterintopic :
            mqtttopic = conf.mqtttopic + "/" + deviceid
        else: mqtttopic = conf.mqtttopic
    print("\t - " + 'Grott MQTT topic used : ' + mqtttopic)

    if conf.mqttretain:
        if conf.verbose: print("\t - " + 'Grott MQTT message retain enabled')

    try:
        publish.single(mqtttopic, payload=jsonmsg, qos=0, retain=conf.mqttretain, hostname=conf.mqttip,port=conf.mqttport, client_id=conf.inverterid, keepalive=60, auth=conf.pubauth)
        if conf.verbose: print("\t - " + 'MQTT message message sent')
    except TimeoutError:
        if conf.verbose: print("\t - " + 'MQTT connection time out error')
    except ConnectionRefusedError:
        if conf.verbose: print("\t - " + 'MQTT connection refused by target')
    except BaseException as error:
        if conf.verbose: print("\t - " + 'MQTT send failed:', str(error))