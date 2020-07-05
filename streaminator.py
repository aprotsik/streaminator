import click
import yaml
import os

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
    Starts streaminator with value defined in config
    """

    __set_env()
    if streamers:
        os.environ['STREAMERS'] = streamers
    if live:
        os.environ['LIVE_STREAMER'] = live
    os.system('docker-compose up -d')

@main.command()
def stop():
    """
    Stops streaminator
    """

    os.system('docker-compose stop')

@main.command()
@click.option('--live', '-l')
def switch(live):
    """
    Switches streamer to given name
    """

    __set_env()
    os.environ['LIVE_STREAMER'] = live
    os.system('docker-compose stop && docker-compose up -d')

def __parse_config():
    """
    Loads app config
    """
    conf_file = open('streaminator.yaml', 'r')
    conf = yaml.full_load(conf_file)

    return conf

def __set_env():
    """
    Sets needed env vars
    """
    app_conf = __parse_config()

    os.environ['STREAMERS'] = ','.join(app_conf['config']['streamers'])
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

if __name__ == "__main__":
    main()