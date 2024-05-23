import socket
import threading
import configReader
import statusMonitor


class rdtpServer(threading.Thread):
    configs = configReader.readConfig()
    UDPServerSocket = None
    myIP = configs["receiver_ip_addr"]
    myPort = int(configs["receiver_port_number"])

    channelIP = configs["channel_ip_addr"]
    channelPort = int(configs["channel_port_number"])

    bufferSize = 1024
    windowSize = int(configs["receiver_window_size"])
    availableWindow = windowSize
    rcvBase = 0
    rxArr = bytearray()
    LastByteRcvd = 0
    LastByteRead = 0

    windowSeqList = list()

    kill = False
    rxedPkt = list()

    def __init__(self):
        # 데이터그램 소켓을 생성
        self.UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

        # 주소와 IP로 Bind
        self.UDPServerSocket.bind((self.myIP, self.myPort))

        server = threading.Thread(target=self.__startServer)
        server.start()

    def __startServer(self):
        statusMonitor.receiverStatus(0, 0, 0, 0,"INIT", 0, 0, self.windowSeqList.copy())

        # 들어오는 데이터그램 Listen
        while not self.kill:
            # receive slice seq & body
            bytesAddressPair = self.UDPServerSocket.recvfrom(self.bufferSize)

            msg = bytesAddressPair[0]

            txIP = msg[13:22].decode("utf-8")
            txPort = msg[22:26].decode("utf-8")
            seqStartNum = msg[26:36].decode("utf-8")
            lastSeqNum = msg[36:46].decode("utf-8")
            body = msg[46:]
            if body.isalpha() and body.decode("utf-8") == "DONE":
                bytesToSend = str.encode(txIP + txPort + self.myIP + str(self.myPort) + "DONE")
                statusMonitor.receiverStatus(0, 0, 0, 0,"DONE", 0, 0, self.windowSeqList.copy())
                self.kill = True
            elif body.isascii() and body.decode("utf-8").__contains__("REDY"):
                statusMonitor.receiverStatus(0, 0, 0, 0,"REDY", 0, 0, self.windowSeqList.copy())
                isn = int(body[4:].decode("utf-8"))
                rcvBase = isn

                zeros_len = 10 - len(str(isn + 1))
                zeros_str = ''.join("0" for i in range(zeros_len))
                isnStr = zeros_str + str(isn + 1)

                zeros_len = 10 - len(str(self.windowSize))
                zeros_str = ''.join("0" for i in range(zeros_len))
                windowSizeStr = zeros_str + str(self.windowSize)

                bytesToSend = str.encode(txIP + txPort + self.myIP + str(self.myPort) + "REDY" + isnStr + windowSizeStr)
            else:
                # updating rcvBase
                if self.availableWindow < len(body):
                    statusMonitor.receiverStatus(self.rcvBase, self.LastByteRcvd, self.LastByteRcvd,
                                                 self.LastByteRead - 1,
                                                 "STALL", len(self.rxedPkt), self.availableWindow, self.windowSeqList.copy())
                elif int(seqStartNum) == rcvBase and self.availableWindow >= len(body):
                    self.rxArr += body
                    self.availableWindow -= len(body)
                    self.rxedPkt.append(body)
                    self.LastByteRcvd = int(lastSeqNum)
                    self.windowSeqList.append(self.LastByteRcvd)
                    rcvBase = int(lastSeqNum) + 1
                    statusMonitor.receiverStatus(self.rcvBase, self.LastByteRcvd, self.LastByteRcvd, self.LastByteRead - 1,
                                                 "RCV", len(self.rxedPkt), self.availableWindow, self.windowSeqList.copy())

                else:
                    statusMonitor.receiverStatus(self.rcvBase, self.LastByteRcvd, self.LastByteRcvd,
                                                 self.LastByteRead - 1,
                                                 "PASS", len(self.rxedPkt), self.availableWindow, self.windowSeqList.copy())


                # Sending a reply to client
                bytesToSend = str.encode(
                    txIP + txPort + self.myIP + str(self.myPort) + "ACK" + str(rcvBase - 1) + "," + str(
                        len(self.rxArr)))

            self.UDPServerSocket.sendto(bytesToSend, (self.channelIP, self.channelPort))

    def retrieveData(self):
        if len(self.rxedPkt) > 0:
            data = self.rxedPkt[0]
            self.availableWindow += len(data)
            self.rxedPkt.pop(0)
            self.windowSeqList.pop(0)
            self.LastByteRead += len(data)
            statusMonitor.receiverStatus(self.rcvBase, self.LastByteRcvd, self.LastByteRcvd, self.LastByteRead - 1, 0, len(self.rxedPkt), self.availableWindow, self.windowSeqList.copy())
            return data
        elif self.kill:
            return "KILL"
        else:
            return "NONE"

