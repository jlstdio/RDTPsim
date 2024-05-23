import socket
import threading
from packet import packet
import time
import configReader
import statusMonitor


class rdtpClient(threading.Thread):
    configs = configReader.readConfig()
    kill = False
    ttl = int(configs["sender_timeout_value"])
    bufferSize = 1024
    windowSize = int(configs["sender_window_size"])
    totalDataSize = 0
    sliceSize = 128
    availableWindow = windowSize
    rxWindowSize = 0
    LastByteSent = 0
    LastByteWritten = 0
    ACKed = 0

    unSentPkt = list()
    unACKedPkt = dict()
    unACKedSeq = dict()
    windowSeqList = list()

    myIP = configs["sender_ip_addr"]
    myPort = int(configs["sender_port_number"])

    rxIp = None
    rxPort = None

    UDPClientSocket = None
    innerSendRunning = False

    def __init__(self, rxIP, rxPort):
        self.rxIP = rxIP
        self.rxPort = rxPort

        timer = threading.Thread(target=self.__timer)
        timer.start()

        self.UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.UDPClientSocket.bind((self.myIP, self.myPort))

        listener = threading.Thread(target=self.__listener)
        listener.start()

        # handshaking
        initSeq = self.configs["sender_init_seq_no"]
        zeros_len = 10 - len(initSeq)
        zeros = ''.join("0" for i in range(zeros_len))
        bytesToWrite = str.encode("REDY" + zeros + initSeq)
        self.unACKedPkt[0] = bytesToWrite
        packet(self.UDPClientSocket, bytesToWrite, len(bytesToWrite), 0, self.rxIP, self.rxPort, self.myIP,
               self.myPort)

    def __timer(self):
        while not self.kill:
            time.sleep(5)
            if len(self.unACKedPkt) > 0:
                first_key = list(self.unACKedPkt.keys())[0]
                # print(f"{first_key} expired!")
                data = self.unACKedPkt[first_key]
                statusMonitor.senderStatus(self.ACKed, self.LastByteSent, self.ACKed, self.LastByteSent,
                                           self.LastByteWritten, True, len(data), 0, len(self.unACKedPkt),
                                           len(self.unSentPkt), self.windowSeqList.copy())
                packet(self.UDPClientSocket, data, len(data), first_key, self.rxIP, self.rxPort, self.myIP, self.myPort)
                time.sleep(1 / 1000000.0)

    def __innerSend(self):
        self.LastByteWritten = -1
        self.LastByteSent = 0
        self.innerSendRunning = True

        # sending data
        while not self.kill:
            if len(self.unSentPkt) > 0:
                data = self.unSentPkt.pop(0)
                # slice data
                if len(data) < self.sliceSize:
                    dataSize = len(data)
                else:
                    dataSize = self.sliceSize

                # make packet & send
                TTD = time.time() + 5
                bytesToSend = data
                self.unACKedPkt[self.LastByteWritten] = bytesToSend
                self.unACKedSeq[TTD] = self.LastByteWritten
                time.sleep(1 / 1000000.0)
                statusMonitor.senderStatus(self.ACKed, self.LastByteSent, self.ACKed, self.LastByteSent, self.LastByteWritten, True, dataSize, 0, len(self.unACKedPkt),
                                     len(self.unSentPkt), self.windowSeqList.copy())
                packet(self.UDPClientSocket, bytesToSend, dataSize, self.LastByteWritten, self.rxIP, self.rxPort, self.myIP, self.myPort)

                self.LastByteSent = self.LastByteWritten
        self.innerSendRunning = False
        print("file finished")

    def __listener(self):
        print("listener running")
        # wait & print out server response
        while not self.kill:
            unFinishedBytes = 0
            bytesAddressPair = self.UDPClientSocket.recvfrom(self.bufferSize)
            msg = bytesAddressPair[0].decode("utf-8")
            msg = msg[26:]
            addr = bytesAddressPair[1]
            if msg.__contains__("REDY") and not self.innerSendRunning:
                self.rxWindowSize = int(msg[14:24])
                # print(f"Receiver Window is {self.rxWindowSize}")
                self.unACKedPkt.pop(0)
                self.innerSendRunning = True
                thread = threading.Thread(target=self.__innerSend, name='')
                thread.start()

            if msg.__contains__("DONE") and self.innerSendRunning:
                self.kill = True
            elif msg.__contains__("ACK") and self.innerSendRunning:
                refinedMsg = msg.replace("ACK", "")
                refinedMsg = refinedMsg.split(",")
                self.ACKed = int(refinedMsg[0])
                # print(f"ACKed {self.ACKed}")
                key_list = list(self.unACKedSeq.keys())
                val_list = list(self.unACKedSeq.values())
                toBeKilled = list()
                for i in self.unACKedSeq.values():
                    if self.ACKed >= i:
                        toBeKilled.append(i)
                        self.windowSeqList.pop(0)

                for i in toBeKilled:
                    position = val_list.index(int(i))
                    unFinishedBytes = self.totalDataSize - (self.ACKed + 1)
                    self.unACKedSeq.pop(key_list[position], None)
                    returnedWindow = len(self.unACKedPkt.pop(i, None))
                    self.availableWindow += returnedWindow

                '''
                if unFinishedBytes == 0:
                    print("nothing to send")
                '''

                statusMonitor.senderStatus(self.ACKed, self.LastByteSent, self.ACKed, self.LastByteSent, self.LastByteWritten, False, 0, 0,
                                     len(self.unACKedPkt), len(self.unSentPkt), self.windowSeqList.copy())

        print("listener finished")

    def sendData(self, data):
        # print("request to send")
        # check sliding windowSize available size
        if len(data) > self.availableWindow or not self.innerSendRunning:
            return False
        else:
            self.availableWindow -= len(data)
            self.totalDataSize += len(data)
            self.unSentPkt.append(data)
            self.windowSeqList.append(self.totalDataSize)
            # update
            self.LastByteWritten += len(data)
            statusMonitor.senderStatus(self.ACKed, self.LastByteSent, self.ACKed, self.LastByteSent, self.LastByteWritten, False, 0, 0, len(self.unACKedPkt), len(self.unSentPkt), self.windowSeqList.copy())
            return True

    def isOver(self):
        if len(self.unACKedPkt) == 0 and len(self.unSentPkt) == 0:
            bytesToWrite = str.encode("DONE")
            self.unACKedPkt[self.LastByteWritten + 4] = bytesToWrite
            packet(self.UDPClientSocket, bytesToWrite, len(bytesToWrite), 0, self.rxIP, self.rxPort, self.myIP,
                   self.myPort)
            return True
        return False

    def __del__(self):
        print("being killed")
