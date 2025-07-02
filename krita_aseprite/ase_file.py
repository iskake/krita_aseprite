import struct
import zlib

from enum import IntEnum, IntFlag
from typing import NamedTuple as T
from io import BufferedReader

from krita import *
from PyQt5.QtWidgets import QFileDialog


# unsigned int
def read_uint(f: BufferedReader, size: int) -> int:
    return int.from_bytes(f.read(size), byteorder="little", signed=False)

def read_bytes(f: BufferedReader, amount: int) -> bytes:
    return f.read(amount)

# signed int
def read_sint(f: BufferedReader, size: int) -> int:
    return int.from_bytes(f.read(size), byteorder="little", signed=True)

# fixed point
def read_fixed(f: BufferedReader) -> tuple[int,int]:
    # TODO: check if this is correct?
    return (read_uint(f,2), read_uint(f,2))

# floating
def read_float(f: BufferedReader, size: int) -> float:
    return struct.unpack("f", f.read(size))[0]

# pixel
def read_pixels(f: BufferedReader, size: int) -> bytes:
    return f.read(size)

# str
def read_string(f: BufferedReader) -> str:
    length = read_uint(f, 2)
    return f.read(length).decode("utf-8")

def read_ignore(f: BufferedReader, size: int) -> None:
    f.seek(size, 1)



class ChunkType(IntEnum):
    PALETTE_OLD0   = 0x0004
    PALETTE_OLD1   = 0x0011
    LAYER          = 0x2004
    CEL            = 0x2005
    CEL_EXTRA      = 0x2006
    COLOR_PROFILE  = 0x2007
    EXTERNAL_FILES = 0x2008
    MASK           = 0x2016 # Deprecated
    PATH           = 0x2017 # Unused
    TAGS           = 0x2018
    PALETTE        = 0x2019
    USER_DATA      = 0x2020
    SLICE          = 0x2022
    TILESET        = 0x2023

ASE_CHUNK_TYPE_NAMES = {
    ChunkType.PALETTE_OLD0:   "Old palette chunk (0)",
    ChunkType.PALETTE_OLD1:   "Old palette chunk (1)",
    ChunkType.LAYER:          "Layer chunk",
    ChunkType.CEL:            "Cel chunk",
    ChunkType.CEL_EXTRA:      "Cel extra chunk",
    ChunkType.COLOR_PROFILE:  "Color profile chunk",
    ChunkType.EXTERNAL_FILES: "External files chunk",
    ChunkType.MASK:           "Mask chunk (DEPRECATED)",
    ChunkType.PATH:           "Path chunk (UNUSED)",
    ChunkType.TAGS:           "Tags chunk",
    ChunkType.PALETTE:        "Palette chunk",
    ChunkType.USER_DATA:      "User data chunk",
    ChunkType.SLICE:          "Slice chunk",
    ChunkType.TILESET:        "Tileset chunk",
}



class Layer:
    def __init__(
        self,
        layer_flags: int,
        layer_type:  int,
        child_level: int,
        blend_mode:  int,
        opacity: int,
        name: str,
        tileset_idx: int|None,
        uuid: bytes|None,
    ):
        self.layer_flags = layer_flags
        self.layer_type = layer_type
        self.child_level = child_level
        self.blend_mode = blend_mode
        self.opacity = opacity
        self.name = name
        self.tileset_idx = tileset_idx
        self.uuid = uuid

class LayerFlags(IntFlag):
    VISIBLE            = 0b0000_0001
    EDITABLE           = 0b0000_0010
    LOCK_MOVEMENT      = 0b0000_0100
    BACKGROUND         = 0b0000_1000
    PREFER_LINKED_CELS = 0b0001_0000
    GROUP_COLLAPSED    = 0b0010_0000
    REFERENCE_LAYER    = 0b0100_0000

class LayerType(IntEnum):
    NORMAL  = 0
    GROUP   = 1
    TILEMAP = 2

def read_chunk_layer(f: BufferedReader, use_uuid: bool):
    layer_flags = read_uint(f, 2)
    layer_type  = read_uint(f, 2)
    child_level = read_uint(f, 2)
    _layer_width_ignored  = read_ignore(f, 2)
    _layer_height_ignored = read_ignore(f, 2)
    blend_mode = read_uint(f, 2)
    opacity    = read_uint(f, 1)
    _reserved = read_ignore(f, 3)
    name = read_string(f)

    print("      type: ", layer_type)
    print("      flags:", layer_flags)
    print("      child level:", child_level)
    print("      blend mode: ", blend_mode)
    print("      opacity:    ", opacity)
    print("      name:       ", name)

    tileset_idx = read_uint(f, 4) if layer_type == LayerType.TILEMAP else None
    uuid = read_bytes(f, 16) if use_uuid else None

    return Layer(
        layer_flags,
        layer_type,
        child_level,
        blend_mode,
        opacity,
        name,
        tileset_idx,
        uuid
    )



class Cel:
    def __init__(self, layer_idx: int, pos: tuple[int,int], opacity: int, cel_type: int, z_index: int, data: tuple):
        self.layer_idx = layer_idx
        self.pos = pos
        self.opacity = opacity
        self.cel_type = cel_type
        self.z_index = z_index
        self.data = data

        self.flags = None
        self.precise_pos = None
        self.width = None
        self.weight = None

class CelType(IntEnum):
    IMG_RAW      = 0
    LINKED       = 1
    IMG_COMP     = 2
    TILEMAP_COMP = 3

def read_chunk_cel(f: BufferedReader, size: int) -> Cel:
    layer_idx = read_uint(f, 2)
    x_pos     = read_sint(f, 2)
    y_pos     = read_sint(f, 2)
    opacity   = read_uint(f, 1)
    cel_type  = read_uint(f, 2)
    z_index   = read_sint(f, 2)
    _reserved = read_ignore(f,5)
    print("      layer_idx:", layer_idx)
    print("      x_pos:    ", x_pos)
    print("      y_pos:    ", y_pos)
    print("      opacity:  ", opacity)
    print("      cel_type: ", cel_type)
    print("      z_index:  ", z_index)

    match cel_type:
        case CelType.IMG_RAW:
            print("!!cel type is 0!")
            cel_w = read_uint(f, 2)
            cel_h = read_uint(f, 2)
            print("        cel_w:", cel_w)
            print("        cel_h:", cel_h)

            pixels = read_pixels(f, size - sum([2,2,2,1,2,2,5,2,2]))
            print(f"        pixels len: {len(pixels)}")
            data = (cel_w, cel_h, pixels)
        case CelType.LINKED:
            print("        !!cel type is 1!")
            data = read_uint(f, 2)
        case CelType.IMG_COMP:
            print("        !!cel type is 2!")
            cel_w = read_uint(f, 2)
            cel_h = read_uint(f, 2)
            print("        cel_w:", cel_w)
            print("        cel_h:", cel_h)

            pixels_compressed = read_pixels(f, size - sum([2,2,2,1,2,2,5,2,2]))
            pixels = zlib.decompress(pixels_compressed)
            print(f"        pixels len: {len(pixels)}")
            data = (cel_w, cel_h, pixels)
        case CelType.TILEMAP_COMP:
            print("          !!cel type is 3!")
            tiles_w   = read_uint(f, 2)
            tiles_h   = read_uint(f, 2)
            tiles_bpp = read_uint(f, 2)
            bitmask_tile_id   = read_uint(f, 4)
            bitmask_x_flip    = read_uint(f, 4)
            bitmask_y_flip    = read_uint(f, 4)
            bitmask_diag_flip = read_uint(f, 4)
            _reserved = read_ignore(f, 10)
            tiles_compressed = read_bytes(f, size - sum([2,2,2,1,2,2,5,2,2,2,4,4,4,4,10]))
            tiles = zlib.decompress(tiles_compressed)
            data = (
                tiles_w,
                tiles_h,
                tiles_bpp,
                bitmask_tile_id,
                bitmask_x_flip,
                bitmask_y_flip,
                bitmask_diag_flip,
                tiles
            )
            raise NotImplementedError()
        case _: # invalid
            raise Exception(f"Invalid cel type `{cel_type}`")
    return Cel(layer_idx, (x_pos,y_pos), opacity, cel_type, z_index, data)

def read_chunk_cel_extra(f: BufferedReader, cel: Cel) -> None:
    flags = read_uint(f, 4)
    precise_x = read_fixed(f)
    precise_y = read_fixed(f)
    width  = read_fixed(f)
    height = read_fixed(f)
    _reserved = read_ignore(f, 16)

    cel.flags = flags
    cel.precise_pos = (precise_x, precise_y)
    cel.width = width
    cel.height = height



# TODO? replace with just `list[Cel]`?
class Frame:
    def __init__(self, cels: list[Cel]):
        self.cels = cels



class ColorProfile:
    def __init__(self, profile_type: int, flags: bool, gamma: tuple[int,int], data: bytes|None = None):
        self.profile_type = profile_type
        self.flags = flags
        self.gamma = gamma
        self.data = data

class ColorProfileType(IntEnum):
    PROFILE_NONE = 0
    PROFILE_SRGB = 1
    PROFILE_ICC  = 2

def read_chunk_color_profile(f: BufferedReader) -> ColorProfile:
    profile_type  = read_uint(f, 2)
    profile_flags = read_uint(f, 2)
    gamma = read_fixed(f)
    _reserved = read_ignore(f,8)

    print("      type: ", profile_type)
    print("      flags:", profile_flags)
    print("      gamma:", gamma)

    icc_data = None

    if profile_type == ColorProfileType.PROFILE_ICC:
        print("       ICC profile!")
        icc_len = read_uint(f, 4)
        print("       icc data len:", icc_len)
        icc_data = f.read(icc_len)
        print("       icc data:", f"({len(icc_data)} bytes...)")
    return ColorProfile(profile_type, bool(profile_flags), gamma, icc_data)



# TODO: external files chunk



class Tag:
    def __init__(self, from_frame: int, to_frame: int, loop_direction: int, repeat_times: int, name: str) -> None:
        self.from_frame = from_frame
        self.to_frame = to_frame
        self.loop_direction = loop_direction
        self.repeat_times = repeat_times
        self.name = name


def read_tags_chunk(f: BufferedReader) -> list[Tag]:
    num_tags = read_uint(f, 2)
    print("      num tags:", num_tags)
    _reserved0 = read_ignore(f, 8)

    tags = []

    for _ in range(num_tags):
        from_frame = read_uint(f, 2)
        to_frame   = read_uint(f, 2)
        loop_direction = read_uint(f, 1)
        repeat_times   = read_uint(f, 2)

        _reserved1  = read_ignore(f, 6)
        _deprecated = read_ignore(f, 3)
        _reserved2  = read_ignore(f, 1)

        name = read_string(f)

        print("      tag between:", f"{from_frame}-{to_frame}")
        print("      loop dir:", loop_direction)
        print("      repeat:", repeat_times)
        print("      tag name:", name)

        tags.append(Tag(from_frame, to_frame, loop_direction, repeat_times, name))
    return tags


class Color(T):
    r: int
    g: int
    b: int
    a: int
    name: None|str

class Palette:
    def __init__(self, size: int, colors: list[Color]):
        self.size = size
        self.colors = colors

def read_palette_chunk(f: BufferedReader):
    pal_size  = read_uint(f, 4)
    first_idx = read_uint(f, 4)
    last_idx  = read_uint(f, 4)
    _reserved = read_ignore(f, 8)

    print("      pal size:", pal_size)
    print("      first idx:", first_idx)
    print("      last idx: ", last_idx)

    colors = []
    for _ in range(first_idx, last_idx+1):
        flags = read_uint(f, 2)
        r = read_uint(f, 1)
        g = read_uint(f, 1)
        b = read_uint(f, 1)
        a = read_uint(f, 1)
        name = read_string(f) if (flags & 0b1) == 1 else None
        colors.append(Color(r, g, b, a, name))
    return Palette(pal_size, colors)

def read_palette_chunk_old(f: BufferedReader):
    # TODO? does this work correctly for both old chunk ver.0 and ver.1?
    packets  = read_uint(f, 2)

    print("      pal packets:", packets)
    colors = []
    pal_size = 0

    for _ in range(packets):
        _to_skip = read_uint(f, 1)   # ?
        num_colors  = read_uint(f, 1)
        num_colors = 256 if num_colors == 0 else num_colors
        pal_size += num_colors

        for _ in range(num_colors):
            r = read_uint(f, 1)
            g = read_uint(f, 1)
            b = read_uint(f, 1)
            colors.append(Color(r, g, b, 255, None))
    return Palette(pal_size, colors)



# TODO!! actually handle user data for objects/chunks...
class UserData:
    def __init__(self, text: str, color: Color, properties) -> None:
        self.text = text
        self.color = color
        self.properties = properties

def read_user_data_chunk(f: BufferedReader):
    flags = read_uint(f, 4)
    print("      user data flags:", bin(flags))

    text = read_string(f) if (flags & 0b1) != 0 else None

    color = None
    if (flags & 0b10) != 0:
        r = read_uint(f, 1)
        g = read_uint(f, 1)
        b = read_uint(f, 1)
        a = read_uint(f, 1)
        color = Color(r, g, b, a, None)

    properties = None
    if (flags & 0b100) != 0:
        raise NotImplementedError("Properties maps not handled yet")

    print("      text: ", text)
    print("      color:", color)
    print("      properties:", properties)

    return UserData(text, color, properties)



class AsepriteFileHeader:
    def __init__(
        self,
        num_frames: int,
        bounds: tuple[int,int],
        bpp: int,
        flags: int,
        pal_entry: int,
        num_colors: int,
        px_size: tuple[int,int],
        grid: tuple[int,int,int,int]
    ):
        self.num_frames = num_frames
        self.bounds = bounds
        self.bpp = bpp
        self.flags = flags
        self.pal_entry = pal_entry
        self.num_colors = num_colors
        self.px_size = px_size
        self.grid = grid

class AsepriteFileHeaderFlags(IntFlag):
    LAYER_OPACITY_VALID         = 0b001
    LAYER_BLEND_OPACITY_VALID   = 0b010
    LAYER_HAS_UUID              = 0b100

def read_ase_header(f: BufferedReader):
    file_size = read_uint(f, 4)
    magic = read_uint(f, 2)

    print("File size:", file_size)
    print(f"Magic number: 0x{magic:04X} (valid? {magic == 0xA5E0})")

    if magic != 0xA5E0:
        print("Invalid aseprite file! returning...")
        f.close()
        return

    num_frames = read_uint(f, 2)
    width  = read_uint(f, 2)
    height = read_uint(f, 2)
    bpp    = read_uint(f, 2)
    flags  = read_uint(f, 4)

    _speed_deprecated  = read_ignore(f, 2)
    _reserved0 = read_ignore(f,4)
    _reserved1 = read_ignore(f,4)

    pal_entry = read_uint(f,1)

    # 3 ignore bytes
    read_ignore(f, 3)

    num_colors = read_uint(f, 2)

    px_w  = read_uint(f, 1)
    px_h  = read_uint(f, 1)

    grid_x = read_sint(f, 2)
    grid_y = read_sint(f, 2)

    grid_w = read_uint(f, 2)
    grid_h = read_uint(f, 2)

    # 84 zero bytes...
    read_ignore(f, 84)

    print("Frames:", num_frames)
    print("Width: ", width)
    print("Height:", height)
    print("bpp:   ", 8)
    print("flags: ", flags)
    print("trans pal idx:", pal_entry)
    print("colors:", num_colors)
    print("px_w:  ", px_w)
    print("px_h:  ", px_h)
    print("grid_x:", grid_x)
    print("grid_y:", grid_y)
    print("grid_w:", grid_w)
    print("grid_h:", grid_h)

    return AsepriteFileHeader(
        num_frames,
        (width, height),
        bpp,
        flags,
        pal_entry,
        num_colors,
        (px_w, px_h),
        (grid_x, grid_y, grid_w, grid_h)
    )



class AsepriteFile:
    def __init__(
        self,
        header: AsepriteFileHeader,
        palette: Palette,
        layers: list[Layer],
        frames: list[Frame],
        color_profile: ColorProfile,
        # external_files # TODO
        tags: list[Tag],
        user_data: UserData,  #TODO!!!
        # slice     # TODO
        # tileset   # TODO
    ):
        self.header = header
        self.color_profile = color_profile
        self.palette = palette
        self.layers = layers
        self.frames = frames
        # self.external_files = external_files # TODO
        self.tags = tags,
        self.user_data = user_data, #TODO!!!
        #self.slice = slice     # TODO
        #self.tileset = tileset # TODO

def read_ase_file(filename: str):
    with open(filename, "rb") as f:
        header = read_ase_header(f)

        if header is None:
            return

        print()
        print("Individual frames:")

        frames = []
        layers = []
        color_profile = None
        palette = None
        tags = None
        user_data = []

        for frame in range(header.num_frames):
            print(" Frame", frame)
            frame_bytes = read_uint(f, 4)
            frame_magic = read_uint(f, 2)

            if frame_magic != 0xF1FA:
                print("Invalid frame magic number! returning...")
                return

            frame_chunks_old = read_uint(f, 2)
            frame_duration   = read_uint(f, 2)
            _frame_reserved  = read_ignore(f, 2)
            frame_chunks_new = read_uint(f, 4)

            print("  Bytes:", frame_bytes)
            # print("  Valid:", frame_magic == 0xF1FA)
            print("  Duration:", frame_duration)
            print("  Chunks (old):", frame_chunks_old)
            print("  Chunks (new):", frame_chunks_new)

            frame_chunks = frame_chunks_old if frame_chunks_new == 0 else frame_chunks_new

            chunk_types = []
            # TODO: handle for tags etc...

            cels = []

            for chunk in range(frame_chunks):
                print()
                print("  Chunk", chunk)
                chunk_size = read_uint(f, 4)
                print("    Chunk size:", chunk_size)
                chunk_type = read_uint(f, 2)
                print("    Chunk type:", f"0x{chunk_type:04x} ({ASE_CHUNK_TYPE_NAMES[chunk_type]})")

                chunk_size = chunk_size - 4 - 2

                match chunk_type:
                    case ChunkType.PALETTE_OLD0:
                        palette_ = read_palette_chunk_old(f)
                        if palette is None:
                            palette = palette_
                    case ChunkType.PALETTE_OLD1:
                        # TODO: does this one work correctly? (is this chunk ever used anyway...?)
                        palette_ = read_palette_chunk_old(f)
                        if palette is None:
                            palette = palette_
                    case ChunkType.LAYER:
                        layers.append(read_chunk_layer(f, header.flags & 0b100 != 0))
                    case ChunkType.CEL:
                        cels.append(read_chunk_cel(f, chunk_size))
                    case ChunkType.CEL_EXTRA:
                        # TODO: check if this one works too?
                        read_chunk_cel_extra(f, cels[-1])
                    case ChunkType.COLOR_PROFILE:
                        color_profile = read_chunk_color_profile(f)
                    case ChunkType.TAGS:
                        tags = read_tags_chunk(f)
                    case ChunkType.PALETTE:
                        palette = read_palette_chunk(f)
                    case ChunkType.USER_DATA:
                        user_data.append(read_user_data_chunk(f))
                    case _:
                        chunk_data = read_bytes(f, chunk_size)
                        print("    Chunk data:", f"({len(chunk_data)} bytes...)")
                        raise NotImplementedError(f"Currently not implemented for type: {chunk_type}")

                chunk_types.append(chunk_type)
            frames.append(Frame(cels))
            print("  Final chunk types:")
            [print(f"    {ASE_CHUNK_TYPE_NAMES[x]} ({hex(x)})") for x in chunk_types]

        print()
        print("got to the end!")

        return AsepriteFile(
            header,
            palette,
            layers,
            frames,
            color_profile,
            # external_files # TODO
            tags,
            user_data,  #TODO!!!
            # slice     # TODO
            # tileset   # TODO
        )


def write_ase_file(file: AsepriteFile):
    # TODO
    ...


def rgba_to_bgra(data: bytes):
    for i in range(len(data)):
        if i % 4 == 0:
            yield data[i+2]
        elif i % 4 == 2:
            yield data[i-2]
        else:
            yield data[i]

def indexed_to_bgra(data: bytes, pal: Palette):
    for x in data:
        r,g,b,a,_ = pal.colors[x]
        yield b
        yield g
        yield r
        yield a

BLEND_MODES = [
    "normal",
    "multiply",
    "screen",
    "overlay",
    "darken",
    "lighten",
    "dodge",
    "burn",
    "hard_light",
    "soft_light_svg",
    "subtract", # TODO: is `difference` actually different from subtract?
    "exclusion",
    "hue",
    "saturation",
    "color",
    "luminosity_sai", #?
    "addition",
    "subtract",
    "divide",
]

def create_ase_document(ase: AsepriteFile, name: str):
    app = Krita.instance()

    if ase.header.bpp == 16:
        color_mode = "GRAYA"
    else:
        color_mode = "RGBA"

    d = app.createDocument(
        ase.header.bounds[0],
        ase.header.bounds[1],
        name,
        color_mode,
        "U8",
        "",
        300.0
    )

    print("created document!")

    root = d.rootNode()

    parent_node_stack = [root]
    last_node = None
    last_child_level = 0

    nodes = []
    groups_to_collapse = []

    for layer in ase.layers:
        print("Layer name:", layer.name)
        print("child level:", layer.child_level)

        if last_node is not None and layer.child_level != last_child_level:
            if layer.child_level < last_child_level:
                parent_node_stack.pop()
            else:
                parent_node_stack.append(last_node)

        if layer.layer_type == 2:
            raise NotImplementedError("Tilemap layer is not implemented")

        node = d.createNode(
            layer.name,
            "paintLayer" if layer.layer_type == 0 else "groupLayer"
        )

        node.setVisible((layer.layer_flags & LayerFlags.VISIBLE) != 0)
        node.setLocked(not (layer.layer_flags & LayerFlags.EDITABLE) != 0)
        
        if layer.layer_type == LayerType.GROUP and (layer.layer_flags & LayerFlags.GROUP_COLLAPSED) != 0:
            groups_to_collapse.append(node)
            print("!!!!!!!!!!!")
            print("should collapse!!!!")
            print("!!!!!!!!!!!")

        node.setOpacity(255 if layer.layer_type == 1 else layer.opacity)

        node.setBlendingMode(BLEND_MODES[layer.blend_mode])

        parent_node_stack[-1].addChildNode(node, None)
        nodes.append(node)

        last_node = node
        last_child_level = layer.child_level

    for frame in [ase.frames[0]]:
        for cel in frame.cels:
            match cel.cel_type:
                case CelType.IMG_RAW | CelType.IMG_COMP:
                    print("   img cel type!")
                    node = nodes[cel.layer_idx]

                    x, y = cel.pos
                    w, h, data = cel.data

                    if ase.header.bpp == 32:    # RGBA
                        node.setPixelData(bytes(rgba_to_bgra(data)), x, y, w, h)
                    elif ase.header.bpp == 16:  # Grayscale
                        node.setPixelData(data, x, y, w, h)
                    else:                       # Indexed
                        node.setPixelData(bytes(indexed_to_bgra(data, ase.palette)), x, y, w, h)
                case CelType.LINKED:
                    print("   linked cel type!")
                    raise NotImplementedError("Linked cels not implemented... yet")
                case CelType.TILEMAP_COMP:
                    print("   tilemap cel!")
                    raise NotImplementedError("Tilemaps not implemented")

    for node in groups_to_collapse:
        print(node)
        print(node.collapsed())
        node.setCollapsed(True)
        print(node.collapsed())

    d.refreshProjection()

    app.activeWindow().addView(d)
    for node in groups_to_collapse:
        print(node)
        print(node.collapsed())
        node.setCollapsed(True)
        print(node.collapsed())

if __name__ == "__main__":
    file = QFileDialog().getOpenFileName(caption="Open Aseprite file...", filter="Aseprite files (*.ase *.aseprite)")

    print(f"File: {file[0]}" if file[0] else "No file selected!")
    ase_file_name = file[0]

    if not ase_file_name:
        print("No aseprite file! returning...")
    else:
        ase = read_ase_file(ase_file_name)
        if ase is not None:
            print(f"read aseprite file with size {ase.header.bounds} and {ase.header.num_frames} frame(s)")
            create_ase_document(ase, "abcd")