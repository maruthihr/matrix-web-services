import subprocess
import threading
from src.mws import mws
from src.mws_worker_management import t_worker_management

def startEtcd():
    subprocess.run("/home/jai/my-etcd/pre-built-binary/etcd-v3.3.12-linux-amd64/etcd")

if __name__ == '__main__':
    #start the etcd
    # t = threading.Thread(name='startEtcd', target=startEtcd, daemon=True)
    # t.start()

    # start the cli
    #subprocess.run("/home/jai/my-etcd/pre-built-binary/etcd-v3.3.12-linux-amd64/etcd")
    #start the auto scaler thread
    t = threading.Thread(name='worker_management', target=t_worker_management, daemon=True,)
    t.start()

    mws().cmdloop()