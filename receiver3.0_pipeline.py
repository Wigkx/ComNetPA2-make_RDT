import os
from socket import *
import struct
import sys
from logHandler import logHandler
import time


def chksum(data):

    n = 2
    words = [data[i:i+n] for i in range(2,len(data), n)]

    chknum = 0x0
    for w in words:
        chknum += int.from_bytes(w, "big")
        chknum += (chknum & 0x10000) >> 16
        chknum = chknum & 0xFFFF

    chknum = ~chknum & 0xFFFF
    if chknum==int.from_bytes(data[0:2], "big"):
        res = True
    else:
        res = False
        
    return res

if __name__=='__main__':
    try:
        res_filename = sys.argv[1]
        log_filename = sys.argv[2]
    except IndexError:
        print("Usage:")
        print("python receiver.py <result file name> <log file name>")
        sys.exit(1)

    receiverSocket = socket(AF_INET, SOCK_DGRAM)
    receiverSocket.bind(("", 10090))

    print("Ready")

    log_handler = logHandler()
    log_handler.startLogging(log_filename)

    seq = 0
    nowdir = os.getcwd()


    with open(nowdir+"/"+res_filename, 'wb') as file:
        data = receiverSocket.recv(1024)
        while data:
            time.sleep(0.005) # RTT 가정

            srcport = int.from_bytes(data[2:4], "big")

            if chksum(data):
                if (data[4:6] != struct.pack("!H", seq)):
                    log_handler.writeAck(seq, "Wrong Sequence Number")
                    log_handler.writeAck(seq-1, 'Sent Ack')
                    receiverSocket.sendto(struct.pack("!i", seq-1), ("127.0.0.1", srcport))
                else:
                    file.write(data[6:]) # 헤더 짜르기.
                    log_handler.writeAck(seq, 'Sent Ack')
                    receiverSocket.sendto(struct.pack("!i", seq), ("127.0.0.1", srcport))
                    seq += 1 # sender가 보내는 패킷에만 corruption과 drop이 발생한다고 가정합니다.
            else:
                log_handler.writeAck(seq, 'DATA Corrupted') 
                log_handler.writeAck(seq-1, 'Sent Ack')
                receiverSocket.sendto(struct.pack("!i", seq-1), ("127.0.0.1", srcport))

            data = receiverSocket.recv(1024)
        
        #EOF
        log_handler.writeAck(seq, 'Sent Ack')
        receiverSocket.sendto(struct.pack("!i", seq), ("127.0.0.1", srcport))
    print("File transfer is finished.")

    receiverSocket.close()
    log_handler.writeEnd()
    exit(0)