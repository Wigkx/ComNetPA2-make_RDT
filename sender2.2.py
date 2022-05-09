import struct
from PASender import PASender
import sys
import os
from socket import *
from logHandler import logHandler


def makeChksum(data, sourceport):
    res = 0x0
    n = 2
    words = [data[i:i+n] for i in range(0,len(data), n)]
    # 이후 다 더하기. (carry 처리 포함)
    res += sourceport
    res += (res & 0x10000) >> 16
    res = res & 0xFFFF


    for w in words:
        res += int.from_bytes(w, "big")
        res += (res & 0x10000) >> 16
        res = res & 0xFFFF


    return ~res & 0xFFFF

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

    destport = 10090
    sourceport = 10091

    sock = socket(AF_INET, SOCK_DGRAM)
    sock.bind(("", sourceport))
    sender = PASender(sock, config_file="config.txt")

    log_handler = logHandler()
    log_handler.startLogging(log_filename)


    sender.soc.connect(("127.0.0.1", destport))
    print("Connect")


    
    seq = 1 # set current num first
    again = False # and retry bool...

    filelength = os.path.getsize(src_filename)
    with open(src_filename, 'rb') as file:
        data = file.read(1020)
        while data:

            # 이번에 보낼 seq는?
            seq = 1 - seq

            # 과제 목표는 UDP가 아닌 RDT 구현, 일단 여기서 헤더는 체크섬, 길이.
            # 3.0 파이프라인에선 pkt number도 넣을 것.
            chksum = makeChksum(data, sourceport)
            sendData = struct.pack("!HH", chksum, sourceport)+data

            
            if again:
                log_handler.writePkt(seq, "Send DATA Again")
            else:
                log_handler.writePkt(seq, "Send DATA")
            sender.sendto_bytes(sendData, ("127.0.0.1", destport))
            response = sender.soc.recv(4)
            # sender가 보내는 패킷에만 corruption과 drop이 발생한다고 가정합니다.
            
            # ackseq = int.from_bytes(response, "little")
            # if (Seq correct): proceed, toggle Num. else: send again
            if response == bytes(seq):
                log_handler.writePkt(seq, "Sent Successfully")
                data = file.read(1020)
                again = False
            else:
                log_handler.writePkt((1-seq), "Wrong Sequence Number")
                seq = 1 - seq # 위에서 다시 바꿀거 상쇄
                again = True
    # EOF
    while True:

        seq = 1 - seq

        sender.sendto_bytes(bytes(0), (dst_addr, 10090))
        if again:
            log_handler.writePkt(seq, "Send DATA Again")
        else:
            log_handler.writePkt(seq, "Send DATA")

        response = sender.soc.recv(4)
        if response == bytes(seq):
            log_handler.writePkt(seq, "Sent Successfully")
            break
        else:
            log_handler.writePkt((1-seq), "Wrong Sequence Number")
            again = True
            seq = 1 - seq # 위에서 다시 바꿀거 상쇄

    print("File transfer is finished.")

    sender.soc.close()
    log_handler.writeEnd()
    exit(0)