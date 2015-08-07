PI Setup 

```
mkdir ~/projects/
mkdir ~/projects/howmuchcoffee/
mkdir ~/projects/howmuchcoffee/log/
cd ~/projects/howmuchcoffee/
```

copy the files from pi-code into `~/projects/howmuchcoffee/`
edit `start-monitor.sh` to include the slack webhook url

set the host name on the pi to `coffeenpi`

```
chmod +x start-web.sh
chmod +x start-monitor.sh
```

```
sudo apt-get update
sudo apt-get install python-pip
sudo apt-get install libusb-1.0
sudo pip install pyusb==1.0.0b1
```

Do not use 1.0.0b2 it has some bugs that prevent proper operation 

edit cron tab and add the entries in crontab-additions.txt




