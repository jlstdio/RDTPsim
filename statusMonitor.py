import time

unAcked = '\033[32m' + '□' + '\033[0m'
unSent = '\033[31m' + '□' + '\033[0m'
acked = '\033[32m' + '■' + '\033[0m'


def senderStatus(wndwStart=0, wndwEnd=0, LastByteAcked=0, LastByteSent=0, LastByteWritten=0, sent=False, size=0,
                 AckedNum=0, unAckedNum=0, unSentNum=0, windowSeqList = list()):
    print('\033[36m' + "------------------Sender Status------------------" + '\033[0m')
    print('unAcked : ' + unAcked + ' | ' + 'unSent : ' + unSent + ' | ' + 'acked : ' + acked)
    print(f"LastByteAcked {LastByteAcked} | LastByteSent {LastByteSent} | LastByteWritten {LastByteWritten}")
    if sent:
        print(f"sending out data at {time.time()} | size : {size}")
    print(f"Window Status : {wndwStart}[", end="")
    if AckedNum + unAckedNum + unSentNum > 0:
        for i in range(AckedNum):
            print(acked, end="")
        for i in range(unAckedNum):
            if len(windowSeqList) > 0:
                print('\033[32m' + "[" +str(windowSeqList[0]-1) + "]" +'\033[0m', end="")
                windowSeqList.pop(0)
        for i in range(unSentNum):
            if len(windowSeqList) > 0:
                print('\033[31m' + "[" + str(windowSeqList[0]-1) + "]" + '\033[0m', end="")
                windowSeqList.pop(0)
    else:
        print(acked + acked + acked + acked + acked + acked + acked + acked + acked + acked, end="")
    print(f"]{LastByteWritten}")
    print('\033[36m' + "--------------------------------------------------" + '\033[0m')


def receiverStatus(wndwStart=0, wndwEnd=0, LastByteRcvd=0, LastByteRead=0, status=0, pktInWindow=0, windowAvailiable=0, windowSeqList = list()):
    if LastByteRead < 0:
        LastByteRead = 0
    print('\033[36m' + "------------------Receiver Status------------------" + '\033[0m')
    print('unAcked : ' + unAcked + ' | ' + 'unSent : ' + unSent + ' | ' + 'acked : ' + acked)
    print(f"LastByteRcvd {LastByteRcvd} | LastByteRead {LastByteRead} | windowAvailiable {windowAvailiable}")
    if status == "RCV":
        print(f"status : received packet")
    elif status == "PASS":
        print(f"status : ignore packet")
    elif status == "STALL":
        print(f"status : window unavailable")
    elif status == "INIT":
        print(f"status : server initiated and ready")
    elif status == "DONE":
        print(f"status : transition over")
    elif status == "REDY":
        print(f"status : hand-shacked")

    print(f"Window Status : {LastByteRead}[", end="")
    if pktInWindow > 0:
        for i in range(pktInWindow):
            if len(windowSeqList) > 0:
                print('\033[32m' + "[" +str(windowSeqList[0]) + "]" + '\033[0m', end="")
                windowSeqList.pop(0)
    else:
        print("", end="")

    print(f"]{wndwEnd}")
    print('\033[36m' + "--------------------------------------------------" + '\033[0m')
