import os
from socket import *
import sys
from logHandler import logHandler

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


    nowdir = os.getcwd()
    with open(nowdir+"/"+res_filename, 'wb') as file:
        
        try:
            data = receiverSocket.recv(1024)
            while data:
                file.write(data)
                data = receiverSocket.recv(1024) # 이게 마지막 패킷이라면? 판단할 방법은? length 필요할듯 
        except Exception as e:
            print(e)

    print("File transfer is finished.")
    # log_handler.writeEnd()
    receiverSocket.close()
    sys.exit(0)