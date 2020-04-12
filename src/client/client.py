import sys  # using sys.argv
from pathlib import Path  # using Path.rglob()
import os  # using os.path.normpath()
import socket  # using socket.socket()
import zlib  # using zlib.compress()
import hashlib  # using hashlib.md5()


def main():
    try:
        # 获取文件、地址、端口、压缩标志
        path = sys.argv[1]
        addr = sys.argv[2]
        port = int(sys.argv[3])
        compress = len(sys.argv) == 5
        # 发起连接
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((addr, port))
        print(f"connected to {addr}:{port}")
        # 加载所有文件及名称,发送文件
        for f in rread(path):
            send_file(sock, xfile(f[0], f[1], compress=compress))
        # 发送结束位
        sock.send(int(0).to_bytes(4, byteorder='big'))
        print('connection closed')
    except ConnectionRefusedError:
        print('connecttion refused')
    except KeyboardInterrupt:
        print('manual exit')
    sock.close()


def rread(path):
    path = Path(os.path.normpath((Path(path).absolute())))
    return [[path.name, path.read_bytes()]] if path.is_file()\
        else [[item.relative_to(path.parent), item.read_bytes()]
              for item in path.rglob('*')
              if item.is_file()]


class xfile():
    def __init__(self, path, data, compress=False):
        self.name = str(path)
        self.md5 = hashlib.md5(data)
        self.data = zlib.compress(data) if compress else data
        self.name_size = len(self.name.encode('utf-8'))
        self.data_size = len(self.data)
        self.compress = compress


def send_file(sock, path):
    # 发送文件名长度、文件名、摘要和压缩标志
    sock.send(path.name_size.to_bytes(4, byteorder='big'))
    sock.send(path.name.encode('utf-8'))
    sock.send(path.md5.digest())
    sock.send((1 if path.compress else 0).to_bytes(1, byteorder='big'))
    print(f"file: {path.name}, compress:{path.compress}, {path.data_size} Bytes")
    # 获取响应：最大值跳过，其余从指定位置开始传输
    shift = int.from_bytes(sock.recv(8), byteorder='big')
    if (shift == 0xffffffffffffffff):
        print(f"remote file exists, ignored")
        return
    print(f"sending from {shift if shift!=0 else 'start'}")
    # 发送剩余数据长度
    sock.send((path.data_size-shift).to_bytes(8, byteorder='big'))
    while shift + 1024 < len(path.data):
        sock.send(path.data[shift:shift+1024])
        shift += 1024
    sock.send(path.data[shift:])
    print("file sent")


if __name__ == '__main__':
    main()
