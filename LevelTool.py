import gzip
import struct
import math
import json
import base64

class Level:
    def __init__(self):
        self.width = 0
        self.height = 0
        self.depth = 0
        self.blocks = []
        self.xSpawn = 0
        self.ySpawn = 0
        self.zSpawn = 0
        self.rotSpawn = 0

    def format_level_data(self):
        """Format level data in XZY order with length prefix"""
        # Create new array in XZY order
        xzy_blocks = []
        for y in range(self.depth):
            for z in range(self.height):
                for x in range(self.width):
                    index = x + (z * self.width) + (y * self.width * self.height)
                    xzy_blocks.append(self.blocks[index])
        
        # Add length prefix (4 bytes, big endian)
        length = len(xzy_blocks)
        data = struct.pack('>I', length) + bytes(xzy_blocks)
        return gzip.compress(data)
    
    def parse_level_data(self, compressed_data):
        """Parse level data from XZY order with length prefix"""
        # Decompress the data
        decompressed_data = gzip.decompress(compressed_data)
        
        # Extract the length prefix (first 4 bytes, big endian)
        length = struct.unpack('>I', decompressed_data[:4])[0]
        xzy_blocks = decompressed_data[4:4 + length]
        
        # Convert XZY order back to original order
        self.blocks = [0] * (self.width * self.height * self.depth)
        for y in range(self.depth):
            for z in range(self.height):
                for x in range(self.width):
                    index = x + (z * self.width) + (y * self.width * self.height)
                    xzy_index = (y * self.height * self.width) + (z * self.width) + x
                    self.blocks[index] = xzy_blocks[xzy_index]

    def get_chunks(self, compressed_data):
        """Split compressed data into 1024 byte chunks"""
        chunk_size = 1024
        total_length = len(compressed_data)
        total_chunks = math.ceil(total_length / chunk_size)
        chunks = []

        for i in range(total_chunks):
            start = i * chunk_size
            end = min(start + chunk_size, total_length)
            chunk = compressed_data[start:end]
            
            # Pad last chunk if needed
            if len(chunk) < chunk_size:
                chunk = chunk + b'\x00' * (chunk_size - len(chunk))
                
            chunks.append({
                'data': chunk,
                'length': end - start,  # Original length before padding
                'percent': int(((i + 1) / total_chunks) * 100)
            })
        
        return chunks
    
    def modify_block(self, x, y, z, block_id):
        """Modify a block at given coordinates"""
        if 0 <= x < self.width and 0 <= y < self.height and 0 <= z < self.depth:
            index = x + (z * self.width) + (y * self.width * self.depth)
            self.blocks[index] = block_id
        else:
            print(f"Coordinates ({x}, {y}, {z}) are out of bounds for the level size ({self.width}, {self.height}, {self.depth})")

    def save_level(self, filename):
        """Save the level to a file"""
        with open(filename, 'w') as f:
            level_data = {
                'width': self.width,
                'height': self.height,
                'depth': self.depth,
                'blocks': base64.b64encode(self.format_level_data()).decode('utf-8'),
                'xSpawn': self.xSpawn,
                'ySpawn': self.ySpawn,
                'zSpawn': self.zSpawn,
                'rotSpawn': self.rotSpawn
            }
            f.write(json.dumps(level_data))
        print(f"Level saved to {filename}")

def load_level(filename):
    """Load the level from a file"""
    level = Level()
    with open (filename, 'r') as f:
        level_data = json.loads(f.read())
        level.width = level_data['width']
        level.height = level_data['height']
        level.depth = level_data['depth']
        level.parse_level_data(base64.b64decode(level_data['blocks'].encode('utf-8')))
        level.xSpawn = level_data['xSpawn']
        level.ySpawn = level_data['ySpawn']
        level.zSpawn = level_data['zSpawn']
        level.rotSpawn = level_data['rotSpawn']
    print(f"Level loaded from {filename}")
    return level


def make_level(width, height, depth):
    """Create a new level with given dimensions"""
    level = Level()
    level.width = width    # X (width)
    level.height = height  # Z (height)
    level.depth = depth    # Y (depth/length)
    level.blocks = [Blocks.AIR] * (width * height * depth)  # Initialize all blocks to AIR
    level.xSpawn = round(width // 2)  # Spawn point X (middle of width)
    level.ySpawn = math.floor(height // 2) + 1  # Spawn point Y (middle of height)
    level.zSpawn = round(depth // 2)  # Spawn point Z (middle of depth)

    grass_layer_start = (math.floor(height // 2) - 1) * (width * depth)  # Start index of the grass layer (middle of the depth)
    for z in range(depth):
        for x in range(width):
            index = grass_layer_start + x + (z * width)
            level.blocks[index] = Blocks.GRASS  # Set the middle layer to GRASS

    # Set the layer below grass to DIRT
    for y in range(math.floor(height // 2) - 2, -1, -1):  # Start below grass layer and go down to the bottom
        dirt_layer_start = y * (width * depth)
        for z in range(depth):
            for x in range(width):
                index = dirt_layer_start + x + (z * width)
                level.blocks[index] = Blocks.DIRT

    return level

class Blocks:
    AIR = 0
    ROCK = 1
    GRASS = 2
    DIRT = 3
    STONE = 4
    WOOD = 5
    SHRUB = 6
    BLACKROCK = 7
    WATER = 8
    WATERSTILL = 9
    LAVA = 10
    LAVASTILL = 11
    SAND = 12
    GRAVEL = 13
    GOLDROCK = 14
    IRONROCK = 15
    COAL = 16
    TRUNK = 17
    LEAF = 18
    SPONGE = 19
    GLASS = 20
    RED = 21
    ORANGE = 22
    YELLOW = 23
    LIGHTGREEN = 24
    GREEN = 25
    AQUAGREEN = 26
    CYAN = 27
    LIGHTBLUE = 28
    BLUE = 29
    PURPLE = 30
    LIGHTPURPLE = 31
    PINK = 32
    DARKPINK = 33
    DARKGREY = 34
    LIGHTGREY = 35
    WHITE = 36
    YELLOWFLOWER = 37
    REDFLOWER = 38
    MUSHROOM = 39
    REDMUSHROOM = 40
    GOLDSOLID = 41
    IRON = 42
    STAIRCASEFULL = 43
    STAIRCASESTEP = 44
    BRICK = 45
    TNT = 46
    BOOKCASE = 47
    STONEVINE = 48
    OBSIDIAN = 49
