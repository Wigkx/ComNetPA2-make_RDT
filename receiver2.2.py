import os
from socket import *
import sys
from logHandler import logHandler


def chksum(data):

    # 역시 데이터를 전부 word 단위로 끊어 계산.
    n = 4 # 이렇게 4로 하면 되려나? 아니면 비트 단위?
    words = [str(data)[i:i+n] for i in range(0,len(data), n)]


    # 전부+carry까지 더한 뒤, FFFF면 ok
    chknum = 0
    for w in words:
        chknum += int(w)
    chknum += (chknum >> 16)
    chknum = chknum & 0xFFFF
    if chknum==0xFFFF:
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
        print("python sender.py <result file name> <log file name>")
        sys.exit(1)

    receiverSocket = socket(AF_INET, SOCK_STREAM)
    receiverSocket.bind(("127.0.0.1", 10090))
    receiverSocket.listen(1)
    print("Maybe ready")

    connectionSocket, addr = receiverSocket.accept() # 없으면 Transport endpoint is not connected 발생

    log_handler = logHandler()
    log_handler.startLogging(log_filename)

    seq = 0
    nowdir = os.getcwd()
    with open(nowdir+"\\"+res_filename, 'wb') as file:
        data = connectionSocket.recv(1024)
        while data:

            if chksum(data): # 그대로 data 보내면 되나? 혹은 unpack 필요?
                data = data[0:] # 헤더 짜르기. 짜르기 전 전처리가 필요할까? 기준으로 삼을 숫자는?
                file.write(data)
                connectionSocket.send(seq.encode()) # 숫자 1을 전송하는 방법은?
                log_handler.writeAck(seq, 'Sent Ack')
                seq = 1 - seq # sender가 보내는 패킷에만 corruption과 drop이 발생한다고 가정합니다.
            else:
                log_handler.writeAck(1-seq, 'DATA Corrupted')
                connectionSocket.send((1-seq).encode()) # 이렇게 해도 괜찮은가?
                log_handler.writeAck(1-seq, 'Sent Ack')
            
            data = connectionSocket.recv(1024)

    print("File transfer is finished.")

    receiverSocket.close()
    log_handler.writeEnd()
    exit(0)