
text_decode_table = [b' ', b'\xc3\x80', b'\xc3\x81', b'\xc3\x82', b'\xc3\x87', b'\xc3\x88', b'\xc3\x89',
                     b'\xc3\x8a', b'\xc3\x8b', b'\xc3\x8c', b'\x00', b'\xc3\x8e', b'\xc3\x8f',
                     b'\xc3\x92', b'\xc3\x93', b'\xc3\x94', b'\xc5\x92', b'\xc3\x99', b'\xc3\x9a',
                     b'\xc3\x9b', b'\xc3\x91', b'\xc3\x9f', b'\xc3\xa0', b'\xc3\xa1', b'\x00',
                     b'\xc3\xa7', b'\xc3\xa8', b'\xc3\xa9', b'\xc3\xaa', b'\xc3\xab', b'\xc3\xac',
                     b'\x00', b'\xc3\xae', b'\xc3\xaf', b'\xc3\xb2', b'\xc3\xb3', b'\xc3\xb4',
                     b'\xc5\x93', b'\xc3\xb9', b'\xc3\xba', b'\xc3\xbb', b'\xc3\xb1', b'\xc2\xba',
                     b'\xc2\xaa', b'\\e', b'&', b'\\+', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00',
                     b'\\Lv', b'=', b';', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00',
                     b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00',
                     b'\x00', b'\\r', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00',
                     b'\x00', b'\xc2\xbf', b'\xc2\xa1', b'\\pk', b'\\mn', b'\\Po', b'\\Ke', b'\\Bl',
                     b'\\Lo', b'\\Ck', b'\xc3\x8d', b'%', b'(', b')', b'\x00', b'\x00', b'\x00', b'\x00',
                     b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\xc3\xa2', b'\x00', b'\x00',
                     b'\x00', b'\x00', b'\x00', b'\x00', b'\xc3\xad', b'\x00', b'\x00', b'\x00', b'\x00',
                     b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\\au', b'\\ad', b'\\al', b'\\ar',
                     b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\\d', b'\\<',
                     b'\\>', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00',
                     b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00',
                     b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00',
                     b'0', b'1', b'2', b'3', b'4', b'5', b'6', b'7', b'8', b'9', b'!', b'?', b'.', b'-',
                     b'\xe2\x80\xa7', b'.', b'\\qo', b'\\qc', b'\xe2\x80\x98', b"'", b'\\sm', b'\\sf',
                     b'$', b',', b'*', b'/', b'A', b'B', b'C', b'D', b'E', b'F', b'G', b'H', b'I', b'J',
                     b'K', b'L', b'M', b'N', b'O', b'P', b'Q', b'R', b'S', b'T', b'U', b'V', b'W', b'X',
                     b'Y', b'Z', b'a', b'b', b'c', b'd', b'e', b'f', b'g', b'h', b'i', b'j', b'k', b'l',
                     b'm', b'n', b'o', b'p', b'q', b'r', b's', b't', b'u', b'v', b'w', b'x', b'y', b'z',
                     b'\x00', b':', b'\xc3\x84', b'\xc3\x96', b'\xc3\x9c', b'\xc3\xa4', b'\xc3\xb6',
                     b'\xc3\xbc', b'\\?', b'\\btn', b'\\9', b'\\l', b'\\pn', b'\\CC', b'\\\\', b'\n',
                     b'"']


def text_decode(text: bytes) -> str:
    return ''.join([text_decode_table[i].decode() for i in text.split(b'\xFF')[0]])