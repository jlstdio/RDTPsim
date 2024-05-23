from random import randbytes
from rdtpClient import rdtpClient
import time
import os
import configReader
import statusMonitor

# init
configs = configReader.readConfig()
ReceiverIp = configs["receiver_ip_addr"]
ReceiverPort = int(configs["receiver_port_number"])
client = rdtpClient(ReceiverIp, ReceiverPort)
if not os.path.exists("send"):
    os.mkdir("send")
filesList = list()
delayList = list()
statusMonitor.senderStatus()

wSize = True
i = 0
txScenarioPath = configs["sender_scenario_file"]
with open(txScenarioPath, 'r') as f:
    lines = f.readlines()
    for line in lines:
        data = int(line)
        if wSize:
            i += 1
            dummyData = randbytes(data)
            filesList.append(dummyData)
        else:
            delayList.append(data)
        wSize = not wSize

while len(filesList) > 0:
    data = filesList[0]
    result = client.sendData(data)
    if not result:
        time.sleep(0.5)
    else:
        filesList.pop(0)
        if len(delayList) > 0:
            sleepTime = delayList[0]
            delayList.pop(0)
            time.sleep(sleepTime)

while True:
    result = client.isOver()
    if result:
        print("sending done!")
        break
