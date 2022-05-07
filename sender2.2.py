import struct
from tkinter import W
from PASender import PASender
import sys
from socket import *
from logHandler import logHandler


def makeChksum(data):
    res = 0
    # data를 어떻게 word 단위로 더할까?
    n = 4 # 이렇게 4로 하면 되려나? 아니면 비트 단위?
    words = [str(data)[i:i+n] for i in range(0,len(data), n)]

    # 이후 다 더해.
    for w in words:
        res += int(w)

    # carry 더하고 짜르기
    res += (res >> 16)
    res = res & 0xFFFF

    return res

if __name__=='__main__':
    try:
        dst_addr= sys.argv[1]
        window_size = int(sys.argv[2])
        src_filename = sys.argv[3]
        log_filename = sys.argv[4]
    except IndexError:
        print("Usage:")
        print("python sender.py <receiver IP> <window size> <source file name> <log file name>")
        sys.exit(1)

    sock = socket(AF_INET, SOCK_DGRAM)
    sender = PASender(sock, config_file="config.txt")

    log_handler = logHandler()
    log_handler.startLogging(log_filename)

    sourceport = sender.soc.getsockname[1]
    destport = 10090

    sender.soc.connect(("127.0.0.1", destport))
    print("Maybe connect")

    # set current num first

    seq = 1
    again = False
    with open(src_filename, 'rb') as file:
        data = file.read(1016)
        while data:

            # 이번에 보낼 seq는?
            seq = 1 - seq

            # 과제 목표는 UDP가 아닌 RDT 구현, 일단 여기서 헤더는 체크섬 하나만.
            # 3.0 파이프라인에선 pkt number도 넣을 것.
            length = 1024 # 마지막 패킷 보낼 때도 1016+8인가? 아니면 함수를 통해 구해야?
            chksum = makeChksum(data)
            
            data = struct.pack("!Is", chksum, data) # data를 항상 string으로 패킹해도 되나?

            sender.sendto(data, ("127.0.0.1", destport))
            if again:
                log_handler.writePkt(0, "Send DATA Again")
            else:
                log_handler.writePkt(0, "Send DATA")
            
            #Wait for ack, TODO: log
            response, addr = sender.soc.recvfrom(1024) # 이것도 1024바이트?
            # sender가 보내는 패킷에만 corruption과 drop이 발생한다고 가정합니다.
            
            ackseq = 0 # TODO: 받은 패킷에서 Ack 뽑아내기
            
            # if (Seq correct): proceed, toggle Num. else: send again
            if ackseq == seq:
                log_handler.writePkt(seq, "Sent Successfully")
                data = file.read(1024)
                again = False
            else:
                log_handler.writePkt(seq, "Wrong Sequence Number")
                seq = 1 - seq # 위에서 다시 바꿀거 상쇄
                again = True

    print("File transfer is finished.")
    sender.soc.close()
    log_handler.writeEnd()
    exit(0)