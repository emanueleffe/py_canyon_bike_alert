Some spaghetti code to check the availability of a bike on Canyon Website.

Requirements:

* python (tested and developed on 3.9)
* python libraries, just install them with ```pip install -r requirements.txt [--user]```

Configs:

Just set everything you want to change in the script, lines 5-23. You can set if the script will send an email and/or a telegram notification (requires further configuration with telegram!) and if the script must execute endlessly.


Scheduling:

You have two options: 

* schedule with your os scheduler (eg. Windows: task scheduler, Linux: crontab)
* cycle the script endlessly (endless option in configs)

Just launch the script with the following command + parameters:

```
python py_canyon_bike_alert.py urlofthebike cachefileused colour size
```

Example (beware: it must include the colour variant in the url, in this case: ```?dwvar_3092_pv_rahmenfarbe=GN%2FBK```):

```
python py_canyon_bike_alert.py https://www.canyon.com/it-it/gravel-bikes/all-road/grail/al/grail-6/3092.html?dwvar_3092_pv_rahmenfarbe=GN%2FBK cache/grail6forest 'Forest ðŸŸ¢' 'S'
```