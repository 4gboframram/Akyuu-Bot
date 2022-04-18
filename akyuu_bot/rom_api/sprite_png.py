import io
from typing import BinaryIO
from ..sprite_utils import sprites
from .rom import Pointer
from PIL import Image


def get_sprite_data(rom: BinaryIO, sprite_ptr: int, palette_ptr: int) -> bytes:  # to be stored in the database
    # thanks so much to https://github.com/magical/pokemon-gba-sprites for
    # providing the sprite decompression
    sprite_data = sprites.read_sprite(rom, sprite_ptr)
    palette = sprites.read_palette(rom, palette_ptr)

    im = Image.frombytes('P', (64, 64), sprite_data)
    im.putpalette([i << 3 for i in b''.join(palette)])  # make brighter :D

    out_buff = io.BytesIO()

    im = im.resize((256, 256), Image.NEAREST)
    im.save(out_buff, 'PNG', transparency=0)

    out_buff.seek(0)
    return out_buff.read()