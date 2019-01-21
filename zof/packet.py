"""Implements Packet class."""

from .match import to_str

_key_map = {
    'ip_ttl': 'nx_ip_ttl',
    'hop_limit': 'nx_ip_ttl',
    'ipv6_nd_res': 'x_ipv6_nd_res',
    'nxt': 'ip_proto'
}

class Packet(dict):
    """Packet implementation."""

    # Support for common field aliases. These aliases only
    # work when get/set using dot notation.

    @property
    def ip_ttl(self):
        return self['nx_ip_ttl']
    
    @property
    def hop_limit(self):
        return self['nx_ip_ttl']
    
    @property
    def ipv6_nd_res(self):
        return self['x_ipv6_nd_res']
    
    @property
    def nxt(self):
        return self['ip_proto']

    @property
    def src(self):
        return self.get('ipv4_src') or self.get('ipv6_src')

    @property
    def dst(self):
        return self.get('ipv4_dst') or self.get('ipv6_dst')

    @property
    def ext_hdrs(self):
        return self.get('ipv6_exthdr', 0) != 0

    __getattr__ = dict.__getitem__

    def __setattr__(self, key, value):
        self[_key_map.get(key, key)] = value

    _PROTO_FIELD = {
        'ETHERNET': 'eth_type',
        'ARP': 'arp_op',
        'IPV4': 'ipv4_src',
        'IPV6': 'ipv6_src',
        'ICMPV4': 'icmpv4_type',
        'ICMPV6': 'icmpv6_type',
        'LLDP': 'x_lldp_ttl'
    }

    def get_protocol(self, protocol):
        """Check if Packet is of specified type and return `self`.

        Return None if packet does not match specified protocol name. This API is
        intended to be similar to RYU's. The implementation is not intended to
        exhaustively check every field; the oftr tool is reponsible for
        populating all necessary protocol fields.
        """
        if Packet._PROTO_FIELD[protocol.upper()] in self:
            return self
        return None

    @classmethod
    def zof_packet_from_field_list(cls, fields):
        """Construct a Packet from a list of fields.

        Args:
            fields (List[dict]): Sequence of fields.
        """
        assert isinstance(fields, list)

        pkt = cls()
        for field in fields:
            key = field['field'].lower()
            value = field['value']
            if key in pkt:
                orig_value = pkt[key]
                if isinstance(orig_value, list):
                    orig_value.append(value)
                else:
                    pkt[key] = [orig_value, value]
            else:
                pkt[key] = value
        return pkt

    def zof_packet_to_field_list(self):
        """Return as list of fields."""
        result = []
        for key, value in self.items():
            if isinstance(value, list):
                for repeated_value in value:
                    result.append({
                        'field': key.upper(),
                        'value': to_str(repeated_value)
                    })
            else:
                result.append({'field': key.upper(), 'value': to_str(value)})
        return result

    @classmethod
    def zof_from_packet_in(cls, event):
        """Convert packet fields and payload into a Packet object."""
        assert event['type'] == 'PACKET_IN'

        msg = event['msg']
        data = bytes.fromhex(msg['data'])
        pkt = cls.zof_packet_from_field_list(msg.pop('_pkt', []))
        pkt_pos = pkt.pop('x_pkt_pos', 0)
        if pkt_pos > 0:
            pkt['payload'] = data[pkt_pos:]
        msg['pkt'] = pkt
        msg['data'] = data

    @staticmethod
    def zof_to_packet_out(event):
        """Convert Packet object back to packet fields and data."""
        assert event['type'] == 'PACKET_OUT'

        msg = event['msg']
        pkt = msg.pop('pkt', None)
        if pkt is not None:
            payload = pkt.pop('payload', None)
            if payload is not None:
                msg['_pkt_data'] = payload.hex()
            msg['_pkt'] = pkt.zof_packet_to_field_list()
