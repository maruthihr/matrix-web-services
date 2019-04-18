import logging
import docker
import time

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
                        # print('this is lb')
                        pass
                    else:
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
        
        time.sleep(1)

        


        

   

if __name__ == "__main__":
    t_worker_management()