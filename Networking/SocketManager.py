try:
    import socks
except ImportError:
    print("Couldn't import PySocks, note that proxies won't work")
import socket
import threading
import struct
import time

import Crypto.RC4 as RC4
import Constants.PacketIds as PacketId
import Networking.Writer as Writer
import Networking.Reader as Reader
import Networking.PacketHelper as PacketHelper

HEADERSIZE = 5
PORT = 2050

class SocketManager:
    def __init__(self):
        self.hooks = {}
        self.ip = None
        self.sock = None
        self.active = True
        self.connected = False
        self.queue = []
        self.writer = Writer.Writer()
        self.reader = Reader.Reader()
        self.incomming_decoder = RC4.RC4(RC4.INCOMING_KEY)
        self.outgoing_encoder = RC4.RC4(RC4.OUTGOING_KEY)
        self.clientHook = None
        self.hooks_thread = None

    def hook(self, packet_type, func):
        if not self.active:
            print("Socket manager is not active")
            return
        if packet_type in self.hooks.keys():
            print("Packet type", packet_type, "is already hooked to function", self.hooks[packet_type])
            return
        if not PacketHelper.isValidPacket(packet_type) and packet_type != "ANY":
            print("Invalid packet_type:", packet_type)
            return
        self.hooks[packet_type] = func

    def connect(self, ip, proxy):
        if not self.active:
            print("Socket manager is not active")
            return
        if self.connected:
            print("Socket already connected to", self.ip, "disconnect it first")
            return
        else:
            self.ip = ip
            print("Connecting to", self.ip)
        self.incomming_decoder.reset()
        self.outgoing_encoder.reset()
        if proxy:
            self.sock = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
            proxyVersion = socks.SOCKS5 if proxy["type"] == 5 else socks.SOCKS4
            self.sock.set_proxy(proxyVersion, proxy["host"], proxy["port"], True, \
                                              proxy["username"], proxy["password"])
        else:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.ip, PORT))
        self.connected = True
        self.startListeners()

    def startListeners(self):
        if not self.active:
            print("Socket manager is not active")
            return
        if not self.connected:
            print("Socket is not connected")
            return
        self.listen_thread = threading.Thread(target=self._listen)
        self.listen_thread.daemon = True
        self.listen_thread.start()
        if self.hooks_thread is None:
            self.hooks_thread = threading.Thread(target=self._callHooks)
            self.hooks_thread.daemon = True
            self.hooks_thread.start()

    def disconnect(self, join=True):
        if not self.active:
            print("Socket manager is not active")
            return
        if not self.connected:
            print("Socket already disconnected")
            return
        self.connected = False
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()
        self.queue = []
        if join:
            self.listen_thread.join()

    def _listen(self):
        if not self.active:
            print("Socket manager is not active")
            return
        while self.connected:
            recv = None
            try:
                recv = self.sock.recv(HEADERSIZE)
                while len(recv) < HEADERSIZE:
                    recv += self.sock.recv(HEADERSIZE-len(recv))
            except ConnectionResetError:
                print("Client forcefully disconnected from", self.ip)
                if self.connected:
                    self.disconnect(False)
                return
            except ConnectionAbortedError:
                print("Stopped connection to", self.ip)
                if self.connected:
                    self.disconnect(False)
                return
            except OSError:#Socket is closed
                return
            
            packet_id = recv[4]
            size = struct.unpack("!i", recv[:4])[0]
            msg = recv
            while len(msg) < size:
                recv = self.sock.recv(size-len(msg))
                msg += self.incomming_decoder.process(recv)
            try:
                packet_type = PacketId.idToType[packet_id]
            except KeyError:
##                print("Unknown packet id:", packet_id)
##                print(msg)
                continue
            if not "UNKNOWN" in packet_type:
                packet = PacketHelper.createPacket(packet_type)
                self.reader.reset(msg)
                packet.read(self.reader)
                self.queue.append(packet)
    
    def _callHooks(self):
        if not self.active:
            print("Socket manager is not active")
            return
        while self.active:
            if len(self.queue) > 0:
                packet = self.queue.pop(0)
                if not self.clientHook is None:
                    self.clientHook(packet)
            else:
                time.sleep(0.5)

    def sendPacket(self, packet):
        if not self.active:
            print("Socket manager is not active")
            return
        if self.connected:
            self.writer.reset()
            packet.write(self.writer)
            self.writer.writeHeader(PacketId.typeToId[packet.type])
            self.writer.buffer = self.writer.buffer[:5] + self.outgoing_encoder.process(self.writer.buffer[5:])
            try:
                self.sock.sendall(bytes(self.writer.buffer))
            except OSError:#Socket is closed
                return
        else:
            print("Socket is not connected")            
