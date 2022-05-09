import struct
from PASender import PASender
import sys
import os
from socket import *
from logHandler import logHandler


def makeChksum(data, sourceport, seq):
    res = 0x0
    n = 2
    words = [data[i:i+n] for i in range(0,len(data), n)]
    # 이후 다 더하기. (carry 처리 포함)
    res += sourceport
    res += (res & 0x10000) >> 16
    res = res & 0xFFFF
    res += seq
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


    
    seq = 0 # set current num first
    again = False # and retry bool...

    window = {}
    winseq = 0
    sent = 0
    eof = False
    endnum = 0

    filelength = os.path.getsize(src_filename)
    with open(src_filename, 'rb') as file:

        while True:

            try:

                for i in range(seq, winseq+window_size, 1):
                    # read in and pack some datas
                    if (i not in window) and not eof:
                        data = file.read(1018)
                        if not data:
                            eof = True
                            endnum = i-1
                            break
                        chksum = makeChksum(data, sourceport, seq)
                        sendData = struct.pack("!HHH", chksum, sourceport, seq)+data
                        window[i] = sendData
                    
                    # send datas
                    if not eof or (seq <= endnum): # seq num 넘어가버리는 일 방지
                        if again:
                            log_handler.writePkt(seq, "Send DATA Again")
                        else:
                            log_handler.writePkt(seq, "Send DATA")
                        
                        sender.sendto_bytes(window[seq], ("127.0.0.1", destport))
                        sender.soc.settimeout(0.1) # 딜레이 등을 고려해 0.1로 설정
                        seq += 1
                        sent += 1
                    else:
                        break
                


                while sent != 0:

                    response = sender.soc.recv(4)
                    sent -= 1
                    # sender가 보내는 패킷에만 corruption과 drop이 발생한다고 가정합니다.
                
                    # if (Seq correct): proceed window
                    if response == struct.pack("!i", winseq):
                        log_handler.writePkt(winseq, "Sent Successfully")
                        del window[winseq]
                        winseq += 1
                        again = False

                        
                    else:
                        log_handler.writePkt(struct.unpack("!i", response)[0], "Wrong Sequence Number")
                        # ignore

                
            
            
            except timeout:
                
                seq = winseq # Go-back N strategy
                again = True
                log_handler.writeTimeout(winseq)

            if eof and (endnum<winseq): # sent all data
                        break

        # //while

    # EOF
    while True:

        try:

            if again:
                log_handler.writePkt(seq, "Send DATA Again")
            else:
                log_handler.writePkt(seq, "Send DATA")
            
            sender.sendto_bytes(bytes(0), (dst_addr, 10090))
            sender.soc.settimeout(0.01)

            response = sender.soc.recv(4)
            if response == struct.pack("!i", seq):
                log_handler.writePkt(seq, "Sent Successfully")
                break
            else:
                log_handler.writePkt(struct.unpack("!i", response)[0], "Wrong Sequence Number")
                again = True

        except timeout:
            log_handler.writeTimeout(seq)
            again = True


    print("File transfer is finished.")

    sender.soc.close()
    log_handler.writeEnd()
    exit(0)