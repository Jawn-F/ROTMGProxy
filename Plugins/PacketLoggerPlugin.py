from PluginManager import hook, plugin

@plugin(active=True)
class NewTickTrackerPlugin:
    def __init__(self):
        self.log_file = "newtick_packet_log.txt"
        with open(self.log_file, "w") as log:
            log.write(f"==== Packet Log Started ====\n")

    @hook("newtick")  # Hooks only the NewTickPacket
    def onNewTick(self, client, packet):
        # Extract relevant information
        tick_info = {
            "tickId": packet.tickId,
            "tickTime": packet.tickTime,
            "serverRealTimeMS": packet.serverRealTimeMS,
            "serverLastTimeRTTMS": packet.serverLastTimeRTTMS,
            "statuses": []
        }

        # Extract status data from ObjectStatusData
        for status in packet.statuses:
            status_data = {
                "objectId": getattr(status, "objectId", "Unknown"),
                "position": self.format_position(status),
                "stats": self.format_stats(status)
            }
            tick_info["statuses"].append(status_data)

        # Convert to readable format
        formatted_log = f"NewTick Packet: {tick_info}\n"

        # Print to console (for debugging)
        #print(formatted_log)

        # Append to log file
        with open(self.log_file, "a") as log:
            log.write(formatted_log)

    def format_position(self, status):
        """Format the position data into a readable format."""
        if hasattr(status, "pos") and status.pos:
            return f"({status.pos.x}, {status.pos.y})"
        return "Unknown"

    def format_stats(self, status):
        """Extract and format stat data."""
        if hasattr(status, "stats") and status.stats:
            return [{ STAT_NAMES.get(stat.statType, f"UnknownStat-{stat.statType}"): stat.statValue } for stat in status.stats]
        return []

# Define human-readable stat names
STAT_NAMES = {
    0: "MaximumHP",
    1: "HP",
    2: "Size",
    3: "MaximumMP",
    4: "MP",
    5: "Experience",
    6: "Level",
    8: "Attack",
    9: "Defense",
    10: "Speed",
    11: "Dexterity",
    12: "Vitality",
    13: "Wisdom",
    14: "Condition",
    15: "HealthBonus",
    16: "ManaBonus",
    17: "AttackBonus",
    18: "DefenseBonus",
    19: "SpeedBonus",
    20: "DexterityBonus",
    21: "VitalityBonus",
    22: "WisdomBonus",
    23: "Equipment",
    24: "PotionCount",
    25: "HPRegen",
    26: "MPRegen",
    27: "MaxedStats",
    28: "Fame",
    38: "FameBonus",
    47: "FameThreshold",
    50: "NewItem",
    53: "SkillCooldown",
    80: "UnknownStat",
}
