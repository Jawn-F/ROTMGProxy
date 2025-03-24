from Networking.Packets.Packet import Packet
from Data.SlotObjectData import *

class InvResultPacket(Packet):
    def __init__(self):
        self.type = "INVRESULT"
        self.unknownBool = False#Prob success bool
        self.unknownByte = 0
        self.fromSlot = SlotObjectData()
        self.toSlot = SlotObjectData()
        self.unknownInt1 = 0
        self.unknownInt2 = 0
    
    def read(self, reader):
        self.unknownBool = reader.readBool()
        self.unknownByte = reader.readByte()
        self.fromSlot.read(reader)
        self.toSlot.read(reader)
        self.unknownInt1 = reader.readInt32()
        self.unknownInt2 = reader.readInt32()

    def write(self, writer):
        writer.writeBool(self.unknownBool)
        writer.writeByte(self.unknownByte)
        self.fromSlot.write(writer)
        self.toSlot.write(writer)
        writer.writeInt32(self.unknownInt1)
        writer.writeInt32(self.unknownInt2)
