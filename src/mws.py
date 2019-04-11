from cmd import Cmd
import docker
import socket
from contextlib import closing
import os
import etcd
import shutil


from mws_persistance import *
from  NginxConfigBuilder import *

dockerClient = docker.from_env() 
etcdClient = etcd.Client(port=2379)
application_image = "webserver_flask"
lb_image = "mws-nginx"
nginx_configs_dir = 'nginx-congfigs'



class mws(Cmd):
    prompt = 'mws> '
    intro = "Welcome to Matrix Web Services! Type ? to list commands"

    def do_exit(self, inp):
        print("Thanks you for using Matrix Web Services. Bye!")
        return True
    
    def help_exit(self):
        print('exit the application. Shorthand: x q Ctrl-D.')
    
    def do_start(self, inp):
        cmdArgs = inp.split(' ')

        # if more than 2 arguments are passed, invalid command
        if len(cmdArgs) is 2:
            applicationName = cmdArgs[0]
            numOfWorkers = cmdArgs[1]
            # recovery from a crash or if the user is trying to start the app again
            runningWorkerIds = getWorkersForApp(applicationName)
            if not runningWorkerIds:
                # get a free port
                port = self.find_a_free_port()
                # create an nginx config with for this app at this port
                if not os.path.exists(nginx_configs_dir+"/"+applicationName):
                    os.mkdir(nginx_configs_dir+"/"+applicationName) 
                create_nginx_config(port, applicationName)
                # start worker containers and update the nginx config
                for worker in range(int(numOfWorkers)):
                    appContainer = dockerClient.containers.run(application_image, "python app.py", stderr=True, stdin_open=True, remove=True, detach=True)
                    ipAddrs = dockerClient.containers.get(appContainer.id).attrs['NetworkSettings']['Networks']['bridge']['IPAddress']
                    #print("ip addrs {}", ipAddrs)
                    add_server(applicationName, ipAddrs)
                    # save container id in etcd
                    saveAppState(applicationName, appContainer.id)

                # start the load balancer container
                lbContainer = dockerClient.containers.run(lb_image, tty=True, stderr=True, stdin_open=True, ports={str(port)+'/tcp': port},
                                                name=applicationName+"-lb", remove=True, detach=True,
                                                volumes={os.getcwd()+'/'+nginx_configs_dir+"/"+applicationName: {'bind': '/etc/nginx', 'mode': 'ro'}})

                saveLbState(applicationName, lbContainer.id)
                lbContainer.exec_run('nginx -s reload')

                print("{0} started with {1} worker/s at 127.0.0.1:{2}".format(cmdArgs[0], cmdArgs[1], port))
            else:
                print("{0} application already running".format(applicationName))

        else:
            print("Invalid command, see help")
    
    def help_start(self):
        print("Start an application with specified number of workers")
    
    def do_stop(self, inp):
        cmdArgs = inp.split(' ')
        if len(cmdArgs) is 1:
            applicationName = cmdArgs[0]
            # get the worker ids from etcd
            runningWorkerIds = getWorkersForApp(applicationName)
            if not runningWorkerIds:
                print("{0} application is not running".format(applicationName))
            # stop all workers and the load balancer
            else:
                for worker in runningWorkerIds:
                    try:
                        dockerClient.containers.get(worker).stop(timeout=0)
                    except:
                        continue

                lbId = getLbForApp(applicationName)
                if lbId:
                    dockerClient.containers.get(lbId).stop(timeout=0)
                
                deleteLbState(applicationName)
                # delete etcd directory
                deleteAppState(applicationName)

                # delete nginx config file
                shutil.rmtree(nginx_configs_dir+"/"+applicationName, ignore_errors=True)
                
                print("{0} application stopped".format(applicationName))
        else:
            print("Invalid command specification. See help")

    def help_stop(self):
        print("Stop the specified application: stop <application name>")
    
    def do_ls(self, inp):
        cmdArgs = inp.split(' ')
        if len(cmdArgs) is 1:
            applicationName = cmdArgs[0]
            # get the worker ids from etcd
            runningWorkerIds = getWorkersForApp(applicationName)
            if not runningWorkerIds:
                print("{0} application is not running".format(applicationName))
            # stop all workers and the load balancer
            else:
                print("{} workers running for {}".format(len(runningWorkerIds), applicationName))
                print("short_id\t\tlong_id")
                for worker in runningWorkerIds:
                    print(dockerClient.containers.get(worker).short_id+"\t\t"+worker)


    def default(self, inp):
        if inp == 'x' or inp == 'q':
            return self.do_exit(inp)
    
        print("Default: {}".format(inp))

    def find_a_free_port(self):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(('localhost', 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return s.getsockname()[1]
    
    do_EOF = do_exit
    help_EOF = help_exit

if __name__ == '__main__':
    mws().cmdloop()