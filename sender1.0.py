from PASender import PASender
import sys
from socket import *
from logHandler import logHandler

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

    sender.soc.connect((dst_addr, 10090))
    print("Connect")

    with open(src_filename, 'rb') as file:
        
        try:
            data = file.read(1024)
            while data:
                sender.sendto(data, (dst_addr, 10090))
                log_handler.writePkt(0, "Send DATA")
                data = file.read(1024)
        except Exception as e:
            print(e)
        sender.sendto(bytes(0), (dst_addr, 10090))
    print("File transfer is finished.")
    log_handler.writeEnd()
    sender.soc.close()

    sys.exit(0)