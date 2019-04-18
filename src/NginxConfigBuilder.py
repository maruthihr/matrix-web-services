import nginx

from src.initializations import nginx_configs_dir


def create_nginx_config(nginx_port, app_name):
    c = nginx.Conf()
    e = nginx.Events()
    e.add(nginx.Key('worker_connections', '1024'))
    c.add(e)
    h = nginx.Http()

    u = nginx.Upstream(app_name)

    h.add(u)

    s = nginx.Server()
    s.add(
        nginx.Key('listen', str(nginx_port)),
        nginx.Key('server_name', app_name),
        nginx.Location('/',
                       nginx.Key('proxy_pass', 'http://'+app_name),
                       nginx.Key('proxy_set_header', 'Host $host')
                       )
    )

    h.add(s)
    c.add(h)

    nginx.dumpf(c, nginx_configs_dir+"/"+app_name+'/nginx.conf')


def add_server(app_name, app_server_ip_addr):

    c = nginx.loadf(nginx_configs_dir+"/"+app_name+'/nginx.conf')

    h = c.filter('Http')[0]

    c.remove(h)


    u = h.filter('Upstream')[0]
    h.remove(u)

    u.add(nginx.Key('server', str(app_server_ip_addr) + ':3000'))

    h.add(u)
    c.add(h)

    nginx.dumpf(c, nginx_configs_dir+"/"+app_name+'/nginx.conf')


def remove_server(app_name, app_server_ip_addr):

    c = nginx.loadf(nginx_configs_dir+"/"+app_name+'/nginx.conf')

    h = c.filter('Http')[0]
    c.remove(h)

    u = h.filter('Upstream')[0]
    h.remove(u)

    u_upd = nginx.Upstream(app_name)

    for k in u.filter('Key'):
        if not k.value == str(app_server_ip_addr) + ':3000':
            u_upd.add(k)

    h.add(u_upd)
    c.add(h)

    nginx.dumpf(c, nginx_configs_dir+"/"+app_name+'/nginx.conf')

    
def create_nginx_config_1(nginx_port, app_name):
    # add new config only if the config for the given app_name doesn't already exist

    try:
        nginx_configs_dir = 'src/nginx-configs'
        c = nginx.loadf(nginx_configs_dir+"/"+'nginx.conf')
        print(c.filter('Http')[0].as_dict['http ']['server'][0]['server_name'])
        for server in c.servers:
            if server['server_name'] == app_name:
                print(server['server_name'])
                return 0

        h = c.filter('Http')[0]
        c.remove(h)

    except FileNotFoundError:
        c = nginx.Conf()
        e = nginx.Events()
        e.add(nginx.Key('worker_connections', '1024'))
        c.add(e)
        h = nginx.Http()

    u = nginx.Upstream(app_name)
    h.add(u)

    s = nginx.Server()
    s.add(
        nginx.Key('listen', str(nginx_port)),
        nginx.Key('server_name', app_name),
        nginx.Location('/',
                       nginx.Key('proxy_pass', 'http://'+app_name),
                       nginx.Key('proxy_set_header', 'Host $host')
                       )
    )

    h.add(s)
    c.add(h)

    nginx.dumpf(c, nginx_configs_dir+"/"+'nginx.conf')

if __name__ == "__main__":
    nginx_configs_dir = 'src/nginx-configs'
    create_nginx_config_1(12345, 'myapp')
    create_nginx_config_1(6789, 'yourapp')
    create_nginx_config_1(987, 'theirapp')
    #add_server('myappy', '123.123.123.123')



