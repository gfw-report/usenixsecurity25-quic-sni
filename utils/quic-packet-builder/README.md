
### Installation:
```bash
pip install -r requirments.txt
```
### Usage

```bash
❯ python3 build.py -h
usage: build.py [-h] [--header_form HEADER_FORM]
                [--fixed_bit FIXED_BIT]
                [--packet_type PACKET_TYPE]
                [--reserved_bits RESERVED_BITS]
                [--pkt_num_len_bits PKT_NUM_LEN_BITS]
                [--version VERSION]
                [--dcid_len DCID_LEN] [--dcid DCID]
                [--scid_len SCID_LEN] [--scid SCID]
                [--token_len TOKEN_LEN] [--token TOKEN]
                [--length LENGTH] [--payload PAYLOAD]
                [--packet_number PACKET_NUMBER]
                [--additional_data ADDITIONAL_DATA]
                [--sample SAMPLE] [-a] [-s]

Construct a QUIC-like long header packet.

options:
  -h, --help            show this help message and exit
  --header_form HEADER_FORM
                        1-bit header form (default: 1)
  --fixed_bit FIXED_BIT
                        1-bit fixed bit (default: 1)
  --packet_type PACKET_TYPE
                        Packet type (default: 00)
  --reserved_bits RESERVED_BITS
                        2-bit reserved bits (default:
                        00)
  --pkt_num_len_bits PKT_NUM_LEN_BITS
                        2-bit packet number length
                        (default: 00)
  --version VERSION     4-byte version number as hex
                        (e.g., "00000001" for
                        0x00000001). Default: 00000001
  --dcid_len DCID_LEN   Destination Connection ID length
                        (default: 8)
  --dcid DCID           Destination Connection ID in
                        hex. Defaults to random if not
                        provided.
  --scid_len SCID_LEN   Source Connection ID length
                        (default: 8)
  --scid SCID           Source Connection ID in hex.
                        Defaults to random if not
                        provided.
  --token_len TOKEN_LEN
                        Token length (default: 0)
  --token TOKEN         Token in hex. Defaults to random
                        if length > 0 and not provided.
  --length LENGTH       Length of remaining payload.
                        Defaults to payload length.
  --payload PAYLOAD     Payload in hex. Defaults to
                        empty. If empty and length is
                        None, length=0
  --packet_number PACKET_NUMBER
                        Packet number in hex. Defaults
                        to zero value bytes dictated by
                        pkt_num_len_bits.
  --additional_data ADDITIONAL_DATA
                        Set additional data instead of
                        calculating the correct value.
  --sample SAMPLE       Set sample data instead of
                        calculating the correct value.
                        This can be a hex representation
                        or offset from the length field.
  -a                    Print additional data instead of
                        the full packet.
  -s                    Print sample data instead of the
                        full packet.
```

Here's an example of how to generate a QUIC packet with a TLS Client Hello payload and zero-length connection IDs:
```bash
python3 build.py --payload=060040400100003c03030000000000000000000000000000000000000000000000000000000000000000000000010000130000000f000d00000a676f6f676c652e636f6d --scid_len=0 --dcid_len=0
```
