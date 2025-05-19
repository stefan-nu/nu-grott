import time
from datetime import datetime, timedelta
from utils    import format_multi_line


def influx_processing(conf, msg, defined_key, jsondate) :
   
    if conf.verbose :  print("\t - " + "Grott InfluxDB publihing started")
    try:
        import  pytz
    except:
        if conf.verbose :  print("\t - " + "Grott PYTZ Library not installed in Python, influx processing disabled")
        conf.inlyx = False
        return
    try:
        local = pytz.timezone(conf.tmzone)
    except :
        if conf.verbose :
            if conf.tmzone ==  "local":  print("\t - " + "Timezone local specified default timezone used")
            else : print("\t - " + "Grott unknown timezone : ",conf.tmzone,", default timezone used")
        conf.tmzone = "local"
        local = int(time.timezone/3600)
        #print(local)

    if conf.tmzone == "local":
        curtz = time.timezone
        utc_dt = datetime.strptime (jsondate, "%Y-%m-%dT%H:%M:%S") + timedelta(seconds=curtz)
    else :
        naive = datetime.strptime (jsondate, "%Y-%m-%dT%H:%M:%S")
        local_dt = local.localize(naive, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)

    ifdt = utc_dt.strftime ("%Y-%m-%dT%H:%M:%S")
    if conf.verbose :  print("\t - " + "Grott original time : ",jsondate,"adjusted UTC time for influx : ",ifdt)

    # prepare influx json msg dictionary

    # if record is a smart monitor record use datalogserial as measurement (to distinguish from solar record)
    if msg["cmd"] != 32 :
        ifobj = {
                    "measurement" : defined_key["pvserial"],
                    "time"        : ifdt,
                    "fields"      : {}
        }
    else:
        ifobj = {
                    "measurement" : defined_key["datalogserial"],
                    "time"        : ifdt,
                    "fields"      : {}
        }

    for key in defined_key :
        if key != "date" :
            ifobj["fields"][key] = defined_key[key]

    # Create list for influx
    ifjson = [ifobj]

    print("\t - " + "Grott influxdb jsonmsg: ")
    print(format_multi_line("\t\t\t ", str(ifjson)))

    try:
        if (conf.influx2):
            if conf.verbose :  print("\t - " + "Grott write to influxdb v2")
            ifresult = conf.ifwrite_api.write(conf.ifbucket,conf.iforg,ifjson)
        else:
            if conf.verbose :  print("\t - " + "Grott write to influxdb v1")
            ifresult = conf.influxclient.write_points(ifjson)

    except Exception as e:
        print("\t - " + "InfluxDB error ")
        print(e)
        raise SystemExit("Influxdb write error, nu-grott will be stopped")