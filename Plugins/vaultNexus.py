import time
import math
from PluginManager import hook, plugin
from Networking.PacketHelper import createPacket
from Networking.Packets.Outgoing.MovePacket import MovePacket
from Data.WorldPosData import WorldPosData
from Data.MoveRecord import MoveRecord

MAIN_ACCOUNT = "Main account"   # put your main account that you want to use to pm commands to the bots here 

@plugin(active=True)
class VaultNexusFollowPlugin:
    def __init__(self):
        self.vaultPortal = None
        self.shouldEnterVault = False
        self.followTarget = None
        self.following = False
        self.trackedPlayers = {}  # objectId -> (name, position)
        self.lastTickId = -1

    @hook("text")
    def onText(self, client, packet):
        if packet.recipient != client.playerData.name:
            return

        sender = packet.name
        msg = packet.text.lower().strip()

        if sender != MAIN_ACCOUNT:
            print(f"[Ignored] Message from unauthorized sender: {sender}")
            return

        if msg.startswith("follow"):
            parts = msg.split()
            if len(parts) == 2:
                self.followTarget = parts[1]
                self.following = True
                print(f"[Command] Following player: {self.followTarget}")
            else:
                print("[Error] Usage: /tell BotName follow <player>")
        elif msg == "stop":
            self.following = False
            self.followTarget = None
            print("[Command] Stopped following.")
        elif msg == "enter vault":
            self.shouldEnterVault = True
            print("[Command] Preparing to enter vault...")
        elif msg == "nexus":
            print("[Command] Returning to Nexus.")
            client.nexus()

    @hook("update")
    def onUpdate(self, client, packet):
        for obj in packet.newObjs:
            if obj.objectType == 1824:  # Vault portal
                self.vaultPortal = obj
                print(f"[Vault] Detected at ({obj.status.pos.x}, {obj.status.pos.y})")

            # Track all players
            name = None
            for stat in obj.status.stats:
                if stat.statType == 31:  # Name
                    name = stat.strStatValue
                    break

            if name:
                self.trackedPlayers[obj.status.objectId] = (name, obj.status.pos)
                print(f"[Seen] Tracking {name} at ({obj.status.pos.x}, {obj.status.pos.y})")


    @hook("newTick")
    def onNewTick(self, client, packet):
        for status in packet.statuses:
            if status.objectId == client.objectId:
                client.pos = status.pos
                print(f"[Tick] Bot position updated to ({client.pos.x}, {client.pos.y})")

            if self.following and status.objectId in self.trackedPlayers:
                name, target_pos = self.trackedPlayers[status.objectId]
                self.trackedPlayers[status.objectId] = (name, status.pos)
                if name.lower() == self.followTarget.lower():
                    print(f"[Follow] Locked onto {name} with ID {status.objectId}")
                    print(f"[Track] Target {name} is at ({target_pos.x}, {target_pos.y})")

                    # Smooth movement toward target
                    dx = target_pos.x - client.pos.x
                    dy = target_pos.y - client.pos.y
                    dist = math.hypot(dx, dy)

                    if dist > 0.1:  # Only move if far enough away
                        max_step = 1.5  # Max tiles per tick to move
                        factor = min(1.0, max_step / dist)
                        step_x = client.pos.x + dx * factor
                        step_y = client.pos.y + dy * factor

                        new_pos = type(target_pos)(step_x, step_y)
                        client.nextPos = [new_pos]
                        print(f"[Move] Stepping toward ({new_pos.x}, {new_pos.y}) - dist: {dist:.2f}")


    def moveTo(self, client, target_x, target_y, tick_id):
        if tick_id == self.lastTickId:  # Already sent this tick
            return

        self.lastTickId = tick_id

        current_time = int(time.time() * 1000) & 0xFFFFFFFF

        move = MovePacket()
        move.tickId = tick_id
        move.time = current_time

        record = MoveRecord()
        record.time = current_time & 0x7FFFFFFF
        record.pos = WorldPosData(client.pos.x, client.pos.y)
        move.records = [record]

        move.newPos = WorldPosData(target_x, target_y)

        print(f"[Move] Sending move packet to ({target_x}, {target_y}) at time {current_time}")
        client.send(move)

