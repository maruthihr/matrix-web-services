import time
import sys
import docker
import logging

from src.mws_persistance import *
from src.NginxConfigBuilder import *

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
hdlr = logging.FileHandler('auto_scale.log')
logger.addHandler(hdlr)
logger.propagate = False

application_image = "webserver_flask"

dockerClient = docker.from_env()
prevTotalCpuUsage = 0.0



def t_auto_scaling(appName):
    global prevTotalCpuUsage
    prevAdd = 0
    nextAdd = 5
    prevRemove = 0
    nextRemove = 0
    runningWorkers = getWorkersForApp(appName)
    totalCpuUsageBeforeConversion = getTotalCpuUsage(appName)
    totalCpuUsage = int(totalCpuUsageBeforeConversion)
    f = open('data.txt', 'a')
    f.write(str((int(totalCpuUsage))) + ','+ str(len(runningWorkers))+'\n')
    f.close()
    logger.info("Starting the auto scaler for {}".format(appName))
    while True:
        #logger.info("gettig stats")
        runningWorkers = getWorkersForApp(appName)
        totalCpuUsageBeforeConversion = getTotalCpuUsage(appName)
        totalCpuUsage = int(totalCpuUsageBeforeConversion)
        logger.info("1. Total CPU usage {}, prevTotalCpuUsage {}, prevAdd {}, nextAdd {}, preRemove {}, nextRemove {} ".format(totalCpuUsage, prevTotalCpuUsage, prevAdd, nextAdd, prevRemove, nextRemove))
        # scale up if the totalCpuUsage is more than 25% and the delta cpu usage is 5%
        if (totalCpuUsage > 0 and ((totalCpuUsage - prevTotalCpuUsage) >= 1) and totalCpuUsage >= nextAdd): 
            f = open('data.txt', 'a')
            f.write(str((int(nextAdd))) + ','+ str(len(runningWorkers))+'\n')
            f.close()
            # get total cpu usage every 100ms
            # add a worker
            logger.info("Adding a worker")
            appContainer = dockerClient.containers.run(application_image, "python app.py", stderr=True, stdin_open=True, remove=True, detach=True)
            ipAddrs = dockerClient.containers.get(appContainer.id).attrs['NetworkSettings']['Networks']['bridge']['IPAddress']
            #logger.info("ip addrs {}", ipAddrs)
            add_server(appName, ipAddrs)
            # save container id in etcd
            saveAppState(appName, appContainer.id)
            lbId = getLbForApp(appName)
            if lbId:
                dockerClient.containers.get(lbId).exec_run('nginx -s reload')
            # update variables
            prevAdd = nextAdd
            nextAdd = nextAdd + 5
            nextRemove = prevAdd
            prevRemove = nextRemove + 5
                    
            
        elif (totalCpuUsage >= 0) and \
                (((prevTotalCpuUsage - totalCpuUsage) >= 1) or (prevTotalCpuUsage == 0 and totalCpuUsage == 0)) and \
                totalCpuUsage <= nextRemove:
            # remove a worker until only one worker is left
            if len(runningWorkers) > 1:
                f = open('data.txt', 'a')
                f.write(str((int(nextRemove))) + ','+ str(len(runningWorkers))+'\n')
                f.close()
                
                logger.info("Removing a worker")
                # remove a worker from top
                worker = runningWorkers[0]
                # try:
                ipAddrs = dockerClient.containers.get(worker).attrs['NetworkSettings']['Networks']['bridge']['IPAddress']
                dockerClient.containers.get(worker).stop(timeout=0)
                # delete worker from etcd
                deleteWorkerforApp(appName, worker)
                #remove server from the nginx conf
                remove_server(appName, ipAddrs)
                # retrieve lb from etcd, restart nginx
                lbId = getLbForApp(appName)
                if lbId:
                    dockerClient.containers.get(lbId).exec_run('nginx -s reload')

                    # logger.info("Successfully removed {} workers for {}".format(abs(scaleCount), applicationName))
                    # for worker in removedWorkers:
                logger.info("Removed worker " + worker)
        
                # except:
                #     logger.info("Unexpected error:", sys.exc_info()[0])
                #     continue
                #update variables
                prevRemove = nextRemove
                if(nextRemove > 0):
                    nextRemove = nextRemove - 5
                nextAdd = prevRemove
                prevAdd = nextAdd - 5
            else:
                logger.info("Running one worker")
        elif totalCpuUsage == 0:

            # do nothing
            pass
        # if the cpu usage is between 15 and 25
        else: 
            # Nothing to do
            pass
        prevTotalCpuUsage = totalCpuUsage
        logger.info("2. Total CPU usage {}, prevTotalCpuUsage {}, prevAdd {}, nextAdd {}, preRemove {}, nextRemove {} ".format(totalCpuUsage, prevTotalCpuUsage, prevAdd, nextAdd, prevRemove, nextRemove))
        time.sleep(1)

def getTotalCpuUsage(appName):
    perCpuUsageTotal = 0
    # for all running workers, get the cpu usage and sum it up
    runningWorkers = getWorkersForApp(appName)
    for worker in runningWorkers:
        s = dockerClient.containers.get(worker).stats(decode=True)
        prevCpuUsageRaw = float(getCpuUsageFromEtcd(worker+'cpuUsageRaw'))
        prevSysCpuUsageRaw = float(getCpuUsageFromEtcd(worker+'sysCpuUsageRaw'))
        d = next(s)
        a, b, c = calculate_cpu_percent2(d, prevCpuUsageRaw, prevSysCpuUsageRaw)
        setCpuUsageFromEtcd(worker+'cpuUsageRaw', c)
        setCpuUsageFromEtcd(worker+'sysCpuUsageRaw', b)
        perCpuUsageTotal = a + perCpuUsageTotal
    
    return perCpuUsageTotal

def calculate_cpu_percent2(d, previous_cpu, previous_system):
    # import json
    # du = json.dumps(d, indent=2)
    # logger.debug("XXX: %s", du)
    cpu_percent = 0.0
    cpu_total = float(d["cpu_stats"]["cpu_usage"]["total_usage"])
    cpu_delta = cpu_total - previous_cpu
    cpu_system = float(d["cpu_stats"]["system_cpu_usage"])
    system_delta = cpu_system - previous_system
    online_cpus = d["cpu_stats"].get("online_cpus", len(d["cpu_stats"]["cpu_usage"]["percpu_usage"]))
    if system_delta > 0.0:
        cpu_percent = (cpu_delta / system_delta) * online_cpus * 100.0
    #logger.info(cpu_percent, cpu_system, cpu_total)
    return cpu_percent, cpu_system, cpu_total

# round up the number to the nearest multiple of 5
def roundUp(numToRound):
    multiple = 5
    remainder = numToRound % multiple
    if remainder == 0:
        return numToRound
    return numToRound + multiple - remainder


# int roundUp(int numToRound, int multiple)  
# {  
#  if(multiple == 0)  
#  {  
#   return numToRound;  
#  }  

#  int remainder = numToRound % multiple; 
#  if (remainder == 0)
#   {
#     return numToRound; 
#   }

#  return numToRound + multiple - remainder; 
# }

# for testing purpose
if __name__ == "__main__":
    t_auto_scaling('ws')