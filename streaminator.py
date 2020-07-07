import click
import yaml
import os
import shutil
import re
import boto3


@click.group()
def main():
    """
    Streaminator CLI app for re-streaming to multiple platforms
    """
    pass

@main.command()
@click.option('--live', '-l', default=False)
@click.option('--streamers', '-s', default=False)
def start(streamers, live):
    """
    Starts streaminator with values defined in config
    """

    print('Starting streaminator...')
    __set_env(streamers=streamers,live=live)
    os.system('docker-compose up -d')

@main.command()
def stop():
    """
    Stops streaminator
    """

    print('Stopping streaminator...')
    __set_env()
    os.system('docker-compose stop')

@main.command()
@click.option('--live', '-l')
def switch(live):
    """
    Switches streamer to given name
    """

    print(f'Switching live streamer to {live}...')
    __set_env(live=live)
    os.system('docker-compose stop && docker-compose up -d')

@main.command()
@click.option('--live', '-l', default=False)
@click.option('--streamers', '-s', default=False)
@click.option('--region', '-r', default='eu-central-1')
@click.option('--instance_size', '-i', default='t2.micro')
def start_cloud(streamers, live, region, instance_size):
    """
    Starts app in AWS with values defined in config
    """

    conf=__parse_config()

    session = boto3.Session(profile_name='streaminator')
    ec2 = session.client('ec2')
    ecs = session.client('ecs')

    waiter = ec2.get_waiter('instance_status_ok')

    __prepare_compose_cloud(streamers=streamers, live=live)
    os.system(f'ecs-cli configure --cluster streaminator --default-launch-type EC2 --config-name streaminator --region {region}')
    if ecs.describe_clusters(clusters=['streaminator'])['clusters'][0]['status'] != 'ACTIVE':
        print('Getting cloud infrastructure up...')
        os.system(f'ecs-cli up --capability-iam --size 1 --instance-type {instance_size} --cluster-config streaminator --aws-profile streaminator')
        ecs_instance = ec2.describe_instances(
            Filters=[
            {
                'Name': 'tag:aws:cloudformation:stack-name',
                'Values': [
                    'amazon-ecs-cli-setup-streaminator',
                ]
            },
            {
                'Name': 'instance-state-name',
                'Values': [
                    'pending',
                    'running'
                ]
            }
            ]
        )
        ec2.authorize_security_group_ingress(
            GroupId=ecs_instance['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['Groups'][0]['GroupId'],
            IpPermissions=[
                {'IpProtocol': 'tcp',
                'FromPort': conf['config']['live_port'],
                'ToPort': conf['config']['live_port'],
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp',
                'FromPort': 8080,
                'ToPort': 8080,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
            ]
        )
        print('Waiting for cloud instance to become available...')
        waiter.wait(
            InstanceIds = [
                    ecs_instance['Reservations'][0]['Instances'][0]['InstanceId']
                ]
        )
    else:
        print('Cluster already in place')

    if ecs.describe_clusters(clusters=['streaminator'])['clusters'][0]['runningTasksCount'] == 0:
        print('Starting streaminator in the cloud...')
        os.system('ecs-cli compose up --create-log-groups --cluster-config streaminator --aws-profile streaminator')
        ip_address = __get_cloud_ip()
        print('Cloud endpoints for streamers are:')
        for streamer in os.environ['STREAMERS'].split(','):
            print(f'rtmp://{ip_address}:{os.environ["NGINX_LIVE_PORT"]}/{streamer}')
        print(f'Initial live streamer is {os.environ["LIVE_STREAMER"]}')
    else:
        print('Streaminator already running')

@main.command()
def stop_cloud():
    """
    Stops streaminator running in AWS
    """
    print('Stopping streaminator in the cloud...')
    os.system('ecs-cli down --force --cluster-config streaminator --aws-profile streaminator')

@main.command()
@click.option('--live', '-l')
def switch_cloud(live):
    """
    Switches streamer to given name in AWS
    """

    print(f'Switching live streamer to {live}...')
    __prepare_compose_cloud(live=live)
    os.system('ecs-cli compose up --create-log-groups --cluster-config streaminator --aws-profile streaminator')
    shutil.copy2('docker-compose-backup.yml','docker-compose.yml')

@main.command()
def configure_cloud_access():
    """
    Configures Streaminator AWS profile
    """

    os.system('aws configure --profile streaminator')

def __get_cloud_ip():
    """
    Returns connection endpoints for cloud streaminator
    """

    session = boto3.Session(profile_name='streaminator')
    ec2 = session.client('ec2')

    ecs_instance = ec2.describe_instances(
            Filters=[
            {
                'Name': 'tag:aws:cloudformation:stack-name',
                'Values': [
                    'amazon-ecs-cli-setup-streaminator',
                ]
            },
            {
                'Name': 'instance-state-name',
                'Values': [
                    'pending',
                    'running'
                ]
            }
            ]
        )
    ip_address = ecs_instance['Reservations'][0]['Instances'][0]['PublicIpAddress']

    return ip_address

def __parse_config():
    """
    Loads app config
    """
    conf_file = open('streaminator.yml', 'r')
    conf = yaml.full_load(conf_file)

    return conf

def __set_env(streamers=False, live=False):
    """
    Sets needed env vars
    """
    app_conf = __parse_config()

    # Pretty ugly code to transfer beautiful settings from config into container env vars
    if streamers:
        os.environ['STREAMERS'] = streamers
    else:
        os.environ['STREAMERS'] = ','.join(app_conf['config']['streamers'])
    if live:
        os.environ['LIVE_STREAMER'] = live
    else:
        os.environ['LIVE_STREAMER'] = app_conf['config']['live_streamer']
    rtmp_urls = ''
    if app_conf['config']['endpoints']['common_rtmp']['active']:
        for service in app_conf['config']['endpoints']['common_rtmp']['urls']:
            if app_conf['config']['endpoints']['common_rtmp']['urls'].index(service) != 0:
                rtmp_urls += ','
            rtmp_urls += service['endpoint'] + '/' + service['key']
    fb_stream_count = 1
    fb_urls = ''
    stunnel_start_port = 19350
    stunnel_port = stunnel_start_port
    if app_conf['config']['endpoints']['facebook']['active']:
        for key in app_conf['config']['endpoints']['facebook']['keys']:
            if app_conf['config']['endpoints']['facebook']['keys'].index(key) != 0:
                fb_urls += ','
                fb_stream_count += 1
            fb_urls += 'rtmp://' + 'streaminator_stunnel_1' + ':' + str(stunnel_port) + '/' + 'rtmp' + '/' + key
            stunnel_port += 1
    os.environ['STUNNEL_FB_STREAM_COUNT'] = str(fb_stream_count)
    os.environ['NGINX_RTMP_PUSH_URLS'] = ''
    if rtmp_urls:
        os.environ['NGINX_RTMP_PUSH_URLS'] += rtmp_urls
    if fb_urls:
        os.environ['NGINX_RTMP_PUSH_URLS'] += ',' + fb_urls
    os.environ['NGINX_LIVE_PORT'] = str(app_conf['config']['live_port'])
    os.environ['STUNNEL_CLIENT'] = 'yes'
    os.environ['STUNNEL_SERVICE'] = 'fb-live'
    os.environ['STUNNEL_ACCEPT'] = str(stunnel_start_port)
    os.environ['STUNNEL_CONNECT'] = app_conf['config']['endpoints']['facebook']['endpoint'][8:35]

    return ['STREAMERS', 'LIVE_STREAMER', 'STUNNEL_FB_STREAM_COUNT', 'NGINX_RTMP_PUSH_URLS', 'NGINX_LIVE_PORT', 'STUNNEL_CLIENT', 'STUNNEL_SERVICE', 'STUNNEL_ACCEPT', 'STUNNEL_CONNECT']

def __prepare_compose_cloud(streamers=False, live=False):
    """
    AWS ECS Cli doesn't support env vars inside compose file. This function prepares compose file for ecs cli.
    """

    env_vars_list = __set_env(streamers=streamers, live=live)

    shutil.copy2('docker-compose.yml','docker-compose-backup.yml')
    with open('docker-compose.yml', 'r+') as f:
        text = f.read()
        for var in env_vars_list:
           if var == 'STUNNEL_CLIENT':
               text = re.sub(f'\${{{var}}}', f'"{os.environ[var]}"', text)
           text = re.sub(f'\${{{var}}}', os.environ[var], text)
        f.seek(0)
        f.write(text)
        f.truncate()


if __name__ == "__main__":
    main()