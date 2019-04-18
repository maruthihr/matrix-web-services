import etcd

client = etcd.Client(port=2379)


def saveAppState(appName, id):
    client.write('/apps/'+appName, id, append=True)


def getWorkersForApp(appName):
    workerIds = []
    try:
        numWorkers = client.get('/apps/'+appName)
    except:
        return None

    for w in numWorkers.children:
        if w.key != '/apps/'+appName+'/lb':
            workerIds.append(w.value)
    return workerIds

def saveLbState(appName, lbId):
    client.write('/apps/'+appName+'/lb', lbId)

def getLbForApp(appName):
    lbId = None
    try:
        numWorkers = client.get('/apps/'+appName)
    except:
        return None

    for w in numWorkers.children:
        if w.key != '/apps/'+appName+'/lb':
            pass
        else:
            lbId = w.value
    return lbId

def deleteAppState(appName):
    try:
        client.delete('/apps/'+appName, recursive=True)
        return True
    except:
        return None

def deleteLbState(appName):
    try:
        client.delete('/apps/'+appName+'/lb')
        return True
    except:
        return None
   

def deleteWorkerforApp(appName, workerId):
    keyFound = False
    try:
        numWorkers = client.get('/apps/'+appName)
    except:
        return None

    for w in numWorkers.children:
        if w.value == workerId:
            client.delete(w.key)
            keyFound = True
        
    return keyFound

def getCpuUsageFromEtcd(worker):
    if worker in client:
        return client.get(worker).value
    else:
        return 0

def setCpuUsageFromEtcd(worker, val):
    client.write(worker, val)


def getAllWorkers():
    workersDict = {}
    try:
        workers = client.read('/apps/', recursive=True)
    except:
        return None

    for w in workers.children:
        workersDict.update({w.key : w.value})
        # print(workersDict.keys())
        # print(workersDict.values())
    return workersDict


if __name__ == "__main__":
    getAllWorkers()
