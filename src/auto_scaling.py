import time
import sys
import docker

from src.mws_persistance import *
from src.NginxConfigBuilder import *

application_image = "webserver_flask"

dockerClient = docker.from_env()


def t_auto_scaling(appName):
    print("Starting the auto scaler for {}".format(appName))
    while True:
        #print("gettig stats")
        runningWorkers = getWorkersForApp(appName)
        totalCpuUsageBeforeConversion = getTotalCpuUsage(appName)
        # get total cpu usage every 100ms
        totalCpuUsage = int(totalCpuUsageBeforeConversion)
        f = open('data.txt', 'a')
        f.write(str(totalCpuUsageBeforeConversion) + ','+ str(len(runningWorkers))+'\n')
        f.close()
        print("Total CPU usage {} %".format(totalCpuUsage))
        if totalCpuUsage > 25:
            # add a worker
            print("Adding a worker")
            appContainer = dockerClient.containers.run(application_image, "python app.py", stderr=True, stdin_open=True, remove=True, detach=True)
            ipAddrs = dockerClient.containers.get(appContainer.id).attrs['NetworkSettings']['Networks']['bridge']['IPAddress']
            #print("ip addrs {}", ipAddrs)
            add_server(appName, ipAddrs)
            # save container id in etcd
            saveAppState(appName, appContainer.id)
            lbId = getLbForApp(appName)
            if lbId:
                dockerClient.containers.get(lbId).exec_run('nginx -s reload')
                    
            
        elif (totalCpuUsage >= 0) and (totalCpuUsage < 15):
            # remove a worker until only one worker is left
            if len(runningWorkers) > 1:
                print("Removing a worker")
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

                    # print("Successfully removed {} workers for {}".format(abs(scaleCount), applicationName))
                    # for worker in removedWorkers:
                print("Removed worker " + worker)
        
                # except:
                #     print("Unexpected error:", sys.exc_info()[0])
                #     continue
            else:
                print("Running one worker")
        elif totalCpuUsage == 0:
            # do nothing
            pass
        # if the cpu usage is between 15 and 25
        else: 
            # Nothing to do
            pass
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
    #print(cpu_percent, cpu_system, cpu_total)
    return cpu_percent, cpu_system, cpu_total



# for testing purpose
if __name__ == "__main__":
    t_auto_scaling('ws')