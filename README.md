# Streaminator
![alt text](https://github.com/aprotsik/streaminator/blob/master/streaminator.jpg)  

Docker/AWS command-line app for re-streaming to multiple platforms and central streaming management. Able to listen to multiple streams simultaneously. Allows switching live streamers almost seamlessly. Can run both locally and in AWS. With default values that aim for AWS free-tier and almost no costs for running in the cloud.

## Development state
Works fully locally and in AWS.
App currently relies on  
https://hub.docker.com/repository/docker/aprotsik/nginx-rtmp  
https://hub.docker.com/repository/docker/aprotsik/stunnel  
which are kinda forks from other containers which I've slightly changed. This will remain so for a while. I intend to refactor those in future and commit proper dockerfiles to this repo.

## Requirements
1. python 3.8
2. pip
3. docker (for local use)
4. docker-compose (for local use)
5. ecs-cli (for use in AWS)

## OS support
Tested on Windows 10 both from WSL and CMD (Should work on any system which can satisfy requirements)

## How to use locally
Given that you already installed python, pip, docker and docker-compose.
1. Install python libraries via pip:  
```pip install -r requirements.txt```
2. Fill the config file. There's a streaminator.yml.template in the repo. Fill it following the instructions inside and remove .template
3. Make sure your firewall doesn't mess with your incoming/outgoing connections (disable, put some rules, whatever) especially if you intend to use different local machine for running streaminator.
4. Start the app:  
```python streaminator.py start``` It will take all the values from config file and run.  
You can also override streamers list and live streamer (the person that is broadcasting atm) via cmd option.  
```python streaminator.py -s dude1,dude2 -l dude1``` This means there will be two locations for dude1 and dude2 (<your_host>/dude1 and <your_host>/dude2) and dude1 will be broadcasting live. App will receive stream from dude2, but won't broadcast it anywahere.
5. When you need to switch the streamer use:  
```python streaminator.py restart -l dude2``` This will put dude2 live. dude2 will still be able to stream to server, but won't be live anywhere. (!!!IMPORTANT!!! Enable connection retry in your broadcasting software as switch causes a very short downtime and you'll be disconnected. Retry will re-connect you on the fly)
6. When you're done, stop the service:  
```python streaminator.py stop```
7. You can see streaming stats on <your_host>:8080/stat


## How to use in AWS
Given that you already installed python, pip, docker and docker-compose.  
1. Install python libraries via pip:  
```pip install -r requirements.txt```
2. Fill the config file. There's a streaminator.yaml.template in the repo. Fill it following the instructions inside and remove .template
3. Check ecs-param.yml. There's a cloud resource config for cpu and memory settings. Memory amount for both containers together shouldn't be greater than max amount of AWS cloud instance RAM. Defaults are for t2.micro which has ~ 1GB.  
4. Start the app:  
```python streaminator.py start-cloud``` Same options are available for config override: --live and --streamers (see about for details). In addition there's also region and instance settings (--region ot -r and --instance or -i) for choosing AWS region and instance size (!!! WARNING !!! Anything greater than t2.micro will cost you money). If you choose something other than t2.micro don't forget to tweak ecs-params.yml. Once the app is started you'll get the list of endpoints for each streamer.  
5. When you need to switch the streamer use:  
```python streaminator.py restart-cloud -l dude2```
6. When you're done, stop the service:  
```python streaminator.py stop-cloud```  
7. You can see streaming stats on <cloud_host>:8080/stat


