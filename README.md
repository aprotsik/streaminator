# Streaminator
![alt text](https://github.com/aprotsik/streaminator/blob/master/streaminator.jpg)  

Docker/AWS app for re-streaming to multiple platforms. Able to listen to multiple streams simultaneously. Allows switching live streamers almost seamlessly.

## Development state
Works fully locally. Can be put in the cloud manually. AWS orchestration code is WIP.  
App currently relies on  
https://hub.docker.com/repository/docker/aprotsik/nginx-rtmp  
https://hub.docker.com/repository/docker/aprotsik/stunnel  
which are kinda forks from other containers which I've slightly changed. This will remain so for a while. I intend to refactor those in future and commit proper dockerfiles to this repo.

## Requirements
1. Pyton 3
2. pip
3. Docker
4. Docker-compose

## OS support
Tested on Windows 10 both from WSL and CMD (Should work on any system which can satisfy requirements)

## How to use
Given that you already installed python, pip, docker and docker-compose.
1. Install python libraries via pip:  
```pip install -r requirements.txt```
2. Fill the config file. There's a streaminator.yaml.template in the repo. Fill it following the instructions inside and remove .template
3. Make sure your firewall doesn't mess with your incoming/outgoing connections (disable, put some rules, whatever) especially if you intend to use different local machine for running streaminator.
4. Start the app:  
```python streaminator.py start``` It will take all the values from config file and run.  
You can also override streamers list and live streamer (the person that is broadcasting atm) via cmd option.  
```python streaminator.py -s dude1,dude2 -l dude1``` This means there will be two locations for dude1 and dude2 (<your_host>/dude1 and <your_host>/dude2) and dude1 will be broadcasting live. App will receive stream from dude2, but won't broadcast it anywahere.
5. When you need to switch the streamer use:  
```python streaminator.py switch -l dude2``` This will put dude2 live. dude2 will still be able to stream to server, but won't be live anywhere. (!!!IMPORTANT!!! Enable connection retry in your broadcasting software as switch causes a very short downtime and you'll be disconnected. Retry will re-connect you on the fly)
6. When you're done, stop the service:  
```python streaminator.py stop```
7. You can see streaming stats on <your_host>:8080/stat


