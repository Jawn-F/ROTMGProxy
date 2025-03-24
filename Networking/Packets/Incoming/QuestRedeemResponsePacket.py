from Networking.Packets.Packet import Packet

class QuestRedeemResponsePacket(Packet):
    def __init__(self):
        self.type = "QUESTREDEEMRESPONSE"
        self.ok = False
        self.message = ""

    def read(self, reader):
        self.ok = reader.readBool()
        self.message = reader.readStr()

    def write(self, writer):
        writer.writeBool(self.ok)
        writer.writeStr(self.message)
