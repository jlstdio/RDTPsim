import configReader
import statusMonitor


class packet():
    configs = configReader.readConfig()
    channelIP = configs["channel_ip_addr"]
    channelPort = int(configs["channel_port_number"])
    UDPClientSocket = None
    channelAddressPort = (channelIP, channelPort)
    sendPktThread = None
    bufferSize = 1024

    def makePkt(self, bytesToSend, size, rxIP, rxPort, myIP, myPort):

        L3Header = str.encode(rxIP + str(rxPort) + myIP + str(myPort))

        # fetch seq number in front of data
        lastSeqNumStr = str(self.seqNum)
        lastSeqNum = bytearray()
        zeros_last_len = 10 - len(lastSeqNumStr)
        zeros_last = ''.join("0" for i in range(zeros_last_len))
        lastSeqNum = str.encode(zeros_last + lastSeqNumStr)

        seqStartNumStr = str((self.seqNum - size + 1))
        seqStartNum = bytearray()
        zeros_start_len = 10 - len(seqStartNumStr)
        zeros_start = ''.join("0" for i in range(zeros_start_len))
        seqStartNum = str.encode(zeros_start + seqStartNumStr)

        pktToSend = L3Header + seqStartNum + lastSeqNum + bytesToSend
        return pktToSend

    def __send(self, bytesToSend, size, rxIP, rxPort, myIP, myPort):
        pkt = self.makePkt(bytesToSend, size, rxIP, rxPort, myIP, myPort)
        self.UDPClientSocket.sendto(pkt, self.channelAddressPort)
        # print(f"send packet : {self.seqNum} | size : {size}")

    def __init__(self, UDPClientSocket, bytesToSend, size, mSeqNum, rxIP, rxPort, myIP, myPort):
        self.UDPClientSocket = UDPClientSocket
        self.seqNum = mSeqNum
        self.__send(bytesToSend, size, rxIP, rxPort, myIP, myPort)
