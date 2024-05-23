import socket
import threading
import time
import configReader
'''
Ne(No error),
L(Loss) 및
C(Congested)와 같은 채널 동작을 흉내 낸다.

여기서 t (latency),
d (small congestion delay) 및
D (big congestion delay) 값은 parameter로 각각 지정할 수 있다.
'''


def __listener():
    configs = configReader.readConfig()
    bufferSize = 1024
    myIP = str(configs["channel_ip_addr"])
    myPort = int(configs["channel_port_number"])

    print(configs["channel_ip_addr"])
    UDPChannelSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPChannelSocket.bind((myIP, myPort))

    i = 0
    count = 0

    channelBehavior = None
    channelScenario = None
    chScenarioPath = configs["channel_scenario_file"]
    with open(chScenarioPath, 'r') as f:
        channelScenario = f.readline()
        print(f"scenario is {channelScenario}")

    t = int(configs["channel_latency"])  # latency
    d = int(configs["channel_small_congestion_delay"])  # small congestion
    D = int(configs["channel_big_congestion_delay"])  # big congestion

    print("channel process running")
    # wait & print out server response
    while True:
        bytesAddressPair = UDPChannelSocket.recvfrom(bufferSize)
        msg = bytesAddressPair[0]

        rxIP = msg[0:9].decode("utf-8")
        rxPort = msg[9:13].decode("utf-8")
        txIp = msg[13:22].decode("utf-8")
        txPort = msg[22:26].decode("utf-8")

        loss = False
        # behavior as Channel
        if count == 0:
            buff = ""
            channelBehavior = channelScenario[i]
            i += 1
            while True:
                if channelScenario[i] == "*":
                    buff = -1
                    i = -1
                    break
                buff += channelScenario[i]
                i += 1
                if i == len(channelScenario):
                    i = 0
                    break
                elif channelScenario[i].isalpha():
                    break
            if buff != -1:
                count = int(buff)
            else:
                count = "INF"
            print(f"current behavior {channelBehavior} - {count}")

        if channelBehavior == "N":
            time.sleep(t)
        elif channelBehavior == "L":
            loss = True
        elif channelBehavior == "C":
            time.sleep(t + D)
        elif channelBehavior == "c":
            time.sleep(t + d)

        if not loss:
            print(f"from {rxIP}:{rxPort} to {txIp}:{txPort}")
            data = msg
            UDPChannelSocket.sendto(data, (rxIP, int(rxPort)))

        if count != "INF":
            count -= 1


listener = threading.Thread(target=__listener)
listener.start()
