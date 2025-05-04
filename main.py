import asyncio
import struct
import LevelTool
import os
from urllib.request import urlopen, Request
from urllib.error import URLError
from urllib.parse import quote

class MCSnake:
    def __init__(self, host='127.0.0.1', port=25565):
        self.host = host
        self.port = port
        self.clients = set()
        self.ids = 1
        self.users = []
        self.chat = []
        self.writers = set()
        self.player_count = 0
        self.salt = os.urandom(16).hex()
        if os.path.isfile("main.lvl"):
            self.level = LevelTool.load_level("main.lvl")
        else:
            self.level = LevelTool.make_level(128, 64, 128)
            self.level.save_level("main.lvl")

        self.heartbeat_task = None  # Store task reference
        self.public = public  # Store public flag

    async def broadcast_online_periodically(self):
        while True:
            self.broadcast_online()
            await asyncio.sleep(120)

    def broadcast_online(self):
        try:
            # Encode individual parameters, not the whole URL
            encoded_name = quote(name)
            url = f"http://www.classicube.net/server/heartbeat/?name={encoded_name}&port={self.port}&users={self.player_count}&max=100&salt={self.salt}&public=true&web=false&software=MCSnake"
            req = Request(url)
            with urlopen(req) as response:
                print(response.read().decode('utf-8'))
        except URLError as e:
            print(f"Error making request: {e}")

    def decode_packet(self, data):
        packet_id = data[0]
        payload = data[1:]
        try:
            if packet_id == 0x00:
                return {"packet": packet_id, "ver": payload[0], "username": payload[1:64].decode('ascii').strip(' '), "verification": payload[65:128].decode('ascii').strip(' ')}
            elif packet_id == 0x0d:
                return {"packet": packet_id, "message": payload[1:].decode('ascii').strip(' ')}
            elif packet_id == 0x05:
                x, y, z, mode, block_id = struct.unpack('>hhhBB', payload)
                return {"packet": packet_id, "x": x, "y": y, "z": z, "mode": mode, "block_id": block_id}
            elif packet_id == 0x08:
                player_id, x, y, z, yaw, pitch = struct.unpack('>BhhhBB', payload)
                return {"packet": packet_id, "x": x, "y": y, "z": z, "yaw": yaw, "pitch": pitch}
            return None
        except struct.error as e:
            print(f"Error decoding packet: {e}")
            return None
    
    def block_update(self, x, y, z, block_id):
        self.level.modify_block(x, y, z, block_id)
        for writer in self.writers:
            try:
                writer.write(b'\x06' + struct.pack('>h', x) + struct.pack('>h', y) + struct.pack('>h', z) + struct.pack('B', block_id))
            except Exception as e:
                print(f"Error sending block update: {e}")
                raise
    
    def send_map(self, to_send):
        """Format and send level data in chunks"""
        try:

            # Send Level Initialize (0x02)
            to_send.append(b'\x02')
            
            # Format and compress level data
            compressed_data = self.level.format_level_data()
            chunks = self.level.get_chunks(compressed_data)
            
            print(f"Sending {len(chunks)} chunks...")
            
            # Send chunks
            for i, chunk in enumerate(chunks):
                # Send Level Data Chunk (0x03)
                packet = (b'\x03' + 
                        struct.pack('>h', chunk['length']) +  # Chunk length (before padding)
                        chunk['data'] +                       # Chunk data (padded to 1024)
                        struct.pack('B', chunk['percent']))   # Progress percentage
                to_send.append(packet)
                print(f"Added chunk {i+1}/{len(chunks)} ({chunk['percent']}%)")

            # Send Level Finalize (0x04)
            packet = (b'\x04' + 
                    struct.pack('>h', self.level.width) +
                    struct.pack('>h', self.level.height) +
                    struct.pack('>h', self.level.depth))
            to_send.append(packet)
            print("Map data prepared successfully")
            
            to_send.append(b'\x08' + struct.pack('b', -1) + struct.pack('>h', self.level.xSpawn*32) + struct.pack('>h', self.level.ySpawn*32) + struct.pack('>h', self.level.zSpawn*32) + b'\x00' + b'\x00')

            return to_send
        except Exception as e:
            print(f"Error in send_map: {e}")
            return to_send

    def format_string(self, string):
        return string.encode('ascii').ljust(64, b'\x20')
    
    def send_chat(self):
        """Send chat messages to all clients"""
        for writer in self.writers:
            try:
                for message in self.chat:
                    writer.write(message)
            except Exception as e:
                print(f"Error sending chat message: {e}")
                raise
        self.chat.clear()

    def create_player(self, user_id, username):
        """Send chat messages to all clients"""
        for writer in self.writers:
            try:
                writer.write(b'\x07' + struct.pack('b', user_id) + self.format_string(username) + struct.pack('>h', self.level.xSpawn*32) + struct.pack('>h', self.level.ySpawn*32) + struct.pack('>h', self.level.zSpawn*32) + b'\x00' + b'\x00')
            except Exception as e:
                print(f"Error creating player: {e}")
                raise

    def send_players(self, to_send, player_user):
        """Send chat messages to all clients"""
        for user in self.users:
            try:
                if not user == player_user:
                    to_send.append(b'\x07' + struct.pack('b', user["id"]) + self.format_string(user["username"]) + struct.pack('>h', self.level.xSpawn*32) + struct.pack('>h', self.level.ySpawn*32) + struct.pack('>h', self.level.zSpawn*32) + b'\x00' + b'\x00')
            except Exception as e:
                print(f"Error sending players: {e}")
                raise
        return to_send

    def delete_player(self, user_id):
        """Send chat messages to all clients"""
        for writer in self.writers:
            try:
                writer.write(b'\x0c' + struct.pack('b', user_id))
            except Exception as e:
                print(f"Error deleting player: {e}")
                raise

    def move_player(self, user_id, x, y, z, yaw, pitch):
        """Send chat messages to all clients"""
        for writer in self.writers:
            try:
                writer.write(b'\x08' + struct.pack('b', user_id) + struct.pack('>h', x) + struct.pack('>h', y) + struct.pack('>h', z) + struct.pack('B', yaw) + struct.pack('B', pitch))
            except Exception as e:
                print(f"Error moving player: {e}")
                raise

    async def handle_client(self, reader, writer):
        client = writer.get_extra_info('peername')
        self.clients.add(client)
        self.writers.add(writer)
        print(f"New connection from {client}")
        self.player_count += 1
        
        to_send = []
        user = None

        try:
            while True:
                header = await reader.read(1)
                if not header:
                    break
                
                packet_id = struct.unpack('>B', header)[0]
                
                # Determine packet length based on packet ID
                if packet_id == 0x00:
                    packet_length = 130  # Example: Handshake packet
                elif packet_id == 0x0d:
                    packet_length = 65   # Example: Chat message packet
                elif packet_id == 0x05:
                    packet_length = 8    # Example: Block update packet
                elif packet_id == 0x08:
                    packet_length = 9    # Example: Player position packet
                else:
                    print(f"Unknown packet ID: {packet_id}")
                    break
                
                packet_data = header + await reader.read(packet_length)

                # print(f"Raw packet: {packet_data!r}")
                decoded = self.decode_packet(packet_data)
                # print(f"Decoded packet: {decoded}")
                
                if decoded is None:
                    self.chat.append(b'\x0d' + struct.pack('>b', 0) + self.format_string("Error: unknown packet"))
                    print(packet_data)
                    self.send_chat()
                else:
                    if decoded['packet'] == 0x00:
                        # Send server info
                        to_send.append(b'\x00\x07' + self.format_string(name) + self.format_string(motd) + b'\x64')

                        # Create user
                        id = self.ids
                        self.ids += 1
                        user = {"id": id, "username": decoded['username']}
                        self.users.append(user)
                        
                        self.create_player(id, decoded['username'])

                        # Prepare and send map data
                        print("Preparing map data...")
                        to_send = self.send_map(to_send)

                        self.send_players(to_send, user)
                        
                    elif decoded['packet'] == 0x0d and user is not None:
                        # Split message into chunks of 64 characters, accounting for "> " prefix
                        message = f"{user['username']}: {decoded['message']}"
                        first_chunk = message[:64]
                        remaining = message[64:]
                        chunks = [remaining[i:i+62] for i in range(0, len(remaining), 62)]  # 62 to account for "> "
                        
                        self.chat.append(b'\x0d' + struct.pack('>b', user["id"]) + self.format_string(first_chunk))
                        for chunk in chunks:
                            self.chat.append(b'\x0d' + struct.pack('>b', user["id"]) + self.format_string("> " + chunk))
                        self.send_chat()
                    elif decoded['packet'] == 0x05 and user is not None:
                        # Update block and send to all clients
                        x = decoded['x']
                        y = decoded['y']
                        z = decoded['z']
                        block_id = decoded['block_id'] if decoded['mode'] == 0x01 else 0
                        
                        self.block_update(x, y, z, block_id)
                    elif decoded['packet'] == 0x08 and user is not None:
                        self.move_player(user["id"], decoded['x'], decoded['y'], decoded['z'], decoded['yaw'], decoded['pitch'])
                    else:
                        self.chat.append(b'\x0d' + struct.pack('>b', 0) + self.format_string('Error: unknown packet'))
                        print(packet_data)
                        self.send_chat()

                # Send all queued packets
                for response in to_send:
                    try:
                        writer.write(response)
                        await writer.drain()
                    except Exception as e:
                        print(f"Error sending packet: {e}")
                        raise
                        
                to_send.clear()
                
        except Exception as e:
            print(f"Error handling client {client}: {e}")
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception as e:
                print(f"Error closing connection: {e}")
            if client in self.clients:
                self.clients.remove(client)
                self.writers.remove(writer)
            print(f"Connection closed for {client}")
            self.level.save_level("main.lvl")
            self.player_count -= 1
            self.delete_player(user["id"])
            self.users.remove(user)


    async def start(self):
        # Create heartbeat task when server starts
        if self.public:
            self.heartbeat_task = asyncio.create_task(self.broadcast_online_periodically())
        
        server = await asyncio.start_server(
            self.handle_client, self.host, self.port
        )
        print(f"Server listening on {self.host}:{self.port}")
        
        async with server:
            await server.serve_forever()

def load_property(filename, property_name, default):
    """Load a property from a file"""
    with open(filename, 'r') as f:
        for line in f:
            if line.startswith(property_name):
                return line.split('=')[1].strip()
    return default

name = load_property("server.properties", "name", "MCSnake Default Name")
motd = load_property("server.properties", "motd", "MCSnake, a python project.")
public = load_property("server.properties", "public", "false").lower() == "true"

if __name__ == "__main__":
    server = MCSnake(load_property("server.properties", "host", '127.0.0.1'), load_property("server.properties", "port", 25565))
    asyncio.run(server.start())