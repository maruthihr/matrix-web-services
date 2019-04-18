import logging
import docker
import time
import os

from src.mws_persistance import *
from src.initializations import *
from src.NginxConfigBuilder import *

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
hdlr = logging.FileHandler('worker_management.log')
logger.addHandler(hdlr)
logger.propagate = False

dockerClient = docker.from_env()

def t_worker_management():
    while True:
        # for all the applications running, check if the workers are running, if any of the workers is not running, start a new worker
        # and cleanup the database
        allWorkers = getAllWorkers()
        if allWorkers is not None:
            for key, value in allWorkers.items():
                # see if the container exists
                try:
                    c = dockerClient.containers.get(value)
                except docker.errors.NotFound:
                    # check if this is a worker or lb
                    temp = key.split('/')
                    applicationName = temp[2]
                    #print(temp)
                    # if 'myws' in temp:
                    #   print('this is myws application')
                    if 'lb' in temp:
                        # if the load balancer is crashed.
                        # get the port number from etcd
                        port = getLbPortForApp(applicationName)
                        if port is not None:
                            # create new nginx lb on the same port
                            # start the load balancer container
                            lbContainer = dockerClient.containers.run(lb_image, tty=True, stderr=True, stdin_open=True, ports={str(port)+'/tcp': port},
                                                            name=applicationName+"-lb", remove=True, detach=True,
                                                            volumes={os.getcwd()+'/'+nginx_configs_dir+"/"+applicationName: {'bind': '/etc/nginx', 'mode': 'ro'}})

                            saveLbState(applicationName, lbContainer.id, port)
                            lbContainer.exec_run('nginx -s reload')

                        # print('this is lb')
                    else:
                        if len(value) == 64:
                            logger.info("Worker {} doesn't exist for application {}".format(value, temp[2]))
                            # create a new worker for this application
                            appContainer = dockerClient.containers.run(application_image, "python app.py", stderr=True, stdin_open=True, remove=True, detach=True)
                            ipAddrs = dockerClient.containers.get(appContainer.id).attrs['NetworkSettings']['Networks']['bridge']['IPAddress']
                            #print("ip addrs {}", ipAddrs)
                            add_server(applicationName, ipAddrs)
                            # save container id in etcd
                            saveAppState(applicationName, appContainer.id)

                            # delete the key from the etcd
                            deleteWorkerforApp(applicationName, value)

                            # start the load balancer container
                            # retrieve lb from etcd, restart nginx
                            lbId = getLbForApp(applicationName)
                            if lbId:
                                try:
                                    dockerClient.containers.get(lbId).exec_run('nginx -s reload')
                                except docker.errors.NotFound:
                                    pass
                except docker.errors.NullResource:
                    pass
        time.sleep(5)

        


        

   

if __name__ == "__main__":
    t_worker_management()