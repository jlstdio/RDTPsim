import os
from rdtpServer import rdtpServer
import time
import configReader

if not os.path.exists("receive"):
    os.mkdir("receive")

server = rdtpServer()

configs = configReader.readConfig()
rxScenarioPath = configs["receiver_scenario_file"]
rxScenario = list()
with open(rxScenarioPath, 'r') as f:
    lines = f.readlines()
    i = True # delay 데이터만 읽음
    for line in lines:
        if i:
            rxScenario.append(int(line))
        i = not i

i = 0 # scenario 순환을 위한 counter
while True:
    result = server.retrieveData()
    if result == "NONE":
        print(f"receiver application sleeps for {rxScenario[i]}")
        time.sleep(rxScenario[i])
        i += 1
        if i >= len(rxScenario):
            i = 0
    elif result == "KILL":
        print("rx done")
        break
