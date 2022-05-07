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
    # receiverSocket.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
    receiverSocket.bind(("", 10090))
    # receiverSocket.listen(1)
    print("listen")

    # connectionSocket, addr = receiverSocket.accept() # accept 안쓰는 코드도 몇개 있던데 일단 이렇게 안하면 왜인지 밑에 recv에서 에러를 뱉는다. (transport endpoint not connected)
    # print("accepted") # 그런데 이게 출력되지 않음. (accept에서 안넘어감. sender의 연결을 못받은 듯함)

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