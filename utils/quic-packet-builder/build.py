import argparse
import secrets

from crypto import QUICCrypto

def encode_varint(value):
    """Encode a value as a QUIC variable-length integer."""
    # For simplicity, only handle up to 4-byte encodings in this example.
    # Extend as needed for larger values.
    if value <= 63:
        # Fits in 6 bits
        return bytes([(value & 0x3f)])  # 00xxxxxx
    elif value <= 16383:
        # Fits in 14 bits
        # 01xxxxxx xxxxxxxx
        return bytes([
            0x40 | ((value >> 8) & 0x3f),
            value & 0xff
        ])
    elif value <= 1073741823:
        # Fits in 30 bits
        # 10xxxxxx xxxxxxxx xxxxxxxx xxxxxxxx
        return bytes([
            0x80 | ((value >> 24) & 0x3f),
            (value >> 16) & 0xff,
            (value >> 8) & 0xff,
            value & 0xff
        ])
    else:
        # For completeness, handle larger values:
        # 11xxxxxx [8-byte total]
        # However, this is not expected for small test values.
        # Raise an error or implement as needed.
        raise ValueError("Value too large for this example's varint encoder.")

def main():
    parser = argparse.ArgumentParser(description='Construct a QUIC-like long header packet.')
    parser.add_argument('--header_form', type=int, default=1, help='1-bit header form (default: 1)')
    parser.add_argument('--fixed_bit', type=int, default=1, help='1-bit fixed bit (default: 1)')
    parser.add_argument('--packet_type', default='00', help='Packet type (default: 00)')
    parser.add_argument('--reserved_bits', default='00', help='2-bit reserved bits (default: 00)')
    parser.add_argument('--pkt_num_len_bits', default='00', help='2-bit packet number length (default: 00)')
    parser.add_argument('--version', default='00000001', help='4-byte version number as hex (e.g., "00000001" for 0x00000001). Default: 00000001')
    parser.add_argument('--dcid_len', type=int, default=8, help='Destination Connection ID length (default: 8)')
    parser.add_argument('--dcid', default=None, help='Destination Connection ID in hex. Defaults to random if not provided.')
    parser.add_argument('--scid_len', type=int, default=8, help='Source Connection ID length (default: 8)')
    parser.add_argument('--scid', default=None, help='Source Connection ID in hex. Defaults to random if not provided.')
    parser.add_argument('--token_len', type=int, default=0, help='Token length (default: 0)')
    parser.add_argument('--token', default=None, help='Token in hex. Defaults to random if length > 0 and not provided.')
    parser.add_argument('--length', type=int, default=None, help='Length of remaining payload. Defaults to payload length.')
    parser.add_argument('--payload', default='', help='Payload in hex. Defaults to empty. If empty and length is None, length=0')
    parser.add_argument('--packet_number', default=None, help='Packet number in hex. Defaults to zero value bytes dictated by pkt_num_len_bits.')
    parser.add_argument('--additional_data', default=None, help='Set additional data instead of calculating the correct value.')
    parser.add_argument('--sample', default=None, help='Set sample data instead of calculating the correct value. This can be a hex representation or offset from the length field.')
    parser.add_argument('-a', action='store_true', help='Print additional data instead of the full packet.')
    parser.add_argument('-s', action='store_true', help='Print sample data instead of the full packet.')

    args = parser.parse_args()

    # Parse and validate bit fields:
    # header_form: 1 bit (0 or 1)
    # fixed_bit:   1 bit (0 or 1)
    # reserved_bits: '00', '01', '10', '11'
    # pkt_num_len_bits: '00', '01', '10', '11'
    hf = 1 if args.header_form != 0 else 0
    fb = 1 if args.fixed_bit != 0 else 0
    
    # Packet type must be two bits:
    if len(args.packet_type) != 2 or any(b not in '01' for b in args.packet_type):
        raise ValueError("packet_type must be a 2-bit string, e.g. '00', '01', '10', '11'.")
    pt = int(args.packet_type, 2)

    # Reserved bits must be two bits:
    if len(args.reserved_bits) != 2 or any(b not in '01' for b in args.reserved_bits):
        raise ValueError("reserved_bits must be a 2-bit string, e.g. '00', '01', '10', '11'.")
    rb = int(args.reserved_bits, 2)

    # Packet number length bits must be two bits:
    if len(args.pkt_num_len_bits) != 2 or any(b not in '01' for b in args.pkt_num_len_bits):
        raise ValueError("pkt_num_len_bits must be a 2-bit string.")
    pnl = int(args.pkt_num_len_bits, 2)

    # Construct header byte:
    # Long header byte: 1 bit header_form, 1 bit fixed_bit, 2 bits reserved, 2 bits pkt_num_len, rest not used here
    # Layout (for a QUIC long header): 1 bit header_form | 1 bit fixed_bit | 2 bits reserved | 2 bits pkt_num_len
    # Example: header_form << 7 | fixed_bit << 6 | reserved_bits << 4 | pkt_num_len
    header_byte = (hf << 7) | (fb << 6) | (pt << 4) | (rb << 2) | pnl

    # Parse version as hex:
    # Expecting a hex string like "00000001" or "ff0000aa", either with or without '0x'.
    version_str = args.version
    if version_str.startswith('0x') or version_str.startswith('0X'):
        version_str = version_str[2:]
    # Ensure the version is 4 bytes (8 hex chars)
    if len(version_str) > 8:
        raise ValueError("Version must fit into 4 bytes (8 hex characters).")
    version_val = int(version_str, 16)
    version_bytes = version_val.to_bytes(4, 'big')

    # Handle Destination Connection ID:
    if args.dcid is None:
        dcid_bytes = secrets.token_bytes(args.dcid_len)
    else:
        dcid_bytes = bytes.fromhex(args.dcid)

    # Handle Source Connection ID:
    if args.scid is None:
        scid_bytes = secrets.token_bytes(args.scid_len)
    else:
        scid_bytes = bytes.fromhex(args.scid)

    # Handle token:
    # If token_len > 0 and token not provided, generate random
    if args.token_len > 0:
        token_length = args.token_len
        if args.token is None:
            token_bytes = secrets.token_bytes(token_length)
        else:
            token_bytes = bytes.fromhex(args.token)
    else:
        token_length = 0
        token_bytes = b''

    token_length_encoded = encode_varint(token_length)

    # Handle Length (the length of the remaining payload, which typically includes packet number and payload):
    # The remaining payload includes Packet Number + Application Data (payload_bytes).
    # By QUIC specification for long headers (e.g. Initial), Length covers the entire remainder of the packet after
    # DCID, SCID, token length, token. It includes packet number and payload. 
    #
    # We'll handle the packet number after we determine its length from pnl.
    # PNL bits + 1 = length in bytes. QUIC initial headers usually have a PN length at least 2, but we’ll trust input.
    pn_len_map = {0:1, 1:2, 2:3, 3:4}
    pn_len = pn_len_map[pnl]

    # Handle payload:
    if args.payload:
        payload_bytes = bytes.fromhex(args.payload)
    else:
        payload_bytes = b''

    # If packet_number not provided, use zero-bytes:
    if args.packet_number is None:
        packet_number_bytes = b'\x00' * pn_len
    else:
        # Parse given packet number
        packet_number_bytes = bytes.fromhex(args.packet_number)
    packet_number_int = int.from_bytes(packet_number_bytes, 'big')

    crypto = QUICCrypto(dcid_bytes, version_val)

    # Now, if length is None, default to len(payload_bytes):
    # Actually in QUIC, length is the length of "packet_number + payload", not just payload.
    # We'll interpret length as the size of packet_number_bytes + payload_bytes.
    if args.length is None:
        length_value = len(packet_number_bytes) + len(payload_bytes) + crypto.aead_key_length
    else:
        length_value = args.length

    length_encoded = encode_varint(length_value)

    packet = bytearray()
    packet.append(header_byte)
    packet.extend(version_bytes)
    packet.append(args.dcid_len)
    packet.extend(dcid_bytes)
    packet.append(args.scid_len)
    packet.extend(scid_bytes)
    packet.extend(token_length_encoded)
    packet.extend(token_bytes)
    packet.extend(length_encoded)
    packet.extend(packet_number_bytes)

    if args.additional_data is not None:
        aad = bytes.fromhex(args.additional_data)
    else:
        aad = bytes(packet)

    if args.a:
        print(aad.hex())
        return

    cipher_payload = crypto.encrypt_packet(True, packet_number_int, aad, payload_bytes)
    if args.sample is not None:
        if args.sample.startswith('0x') or args.sample.startswith('0X') or len(args.sample) > 1:
            sample = bytes.fromhex(args.sample[2:])
        else:
            sample_offset = int(args.sample) - len(packet_number_bytes)
            sample = cipher_payload[sample_offset:sample_offset+16]
    else:
        sample_offset = 4 - len(packet_number_bytes)
        sample = cipher_payload[sample_offset:sample_offset+16]

    (protected_header_byte, protected_packet_number_bytes) = crypto.header_protect(sample, header_byte, packet_number_bytes)
    packet[0] = ord(protected_header_byte)
    packet[-len(packet_number_bytes):] = protected_packet_number_bytes
    packet.extend(cipher_payload)

    if args.s:
        print(sample.hex())
        return

    # Print out the packet in hex:
    print(packet.hex())

if __name__ == '__main__':
    main()
