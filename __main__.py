import subprocess
import threading
from src.mws import mws

def startEtcd():
    subprocess.run("/home/jai/my-etcd/pre-built-binary/etcd-v3.3.12-linux-amd64/etcd")

if __name__ == '__main__':
    #start the etcd
    # t = threading.Thread(name='startEtcd', target=startEtcd, daemon=True)
    # t.start()

    # start the cli
    mws().cmdloop()