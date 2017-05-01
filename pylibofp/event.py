import json
from .objectview import ObjectView, to_json
from .pktview import pktview_from_list

# N.B. An event may have an optional 'async_dispatch' attribute. This is set if
# an async event handler is called, or the event is passed as the result of a
# future to an async task.


class Event(ObjectView):
    """Concrete class that represents an Event."""
    def __init__(self, d):
        super().__init__(d)
        try:
            # Any value with key 'data' MUST be a binary type.
            # If there's no `data` key, the rest of this is skipped.
            self.data = bytes.fromhex(d['data'])
            # If there's no `_pkt_decode` key, the rest is skipped.
            self.pkt = pktview_from_list(d['_pkt_decode'])
            del d['_pkt_decode']
            # If there's no 'x_pkt_pos' key in self.pkt, the rest is skipped.
            self.pkt.payload = self.data[self.pkt['x_pkt_pos']:]
        except KeyError:
            pass


def load_event(event):
    # If `event` is a byte string, decode it as utf-8.
    if isinstance(event, bytes):
        event = event.decode('utf-8')
    try:
        return json.loads(event, object_hook=Event)
    except ValueError as ex:
        # Report malformed JSON input.
        return make_event(event='EXCEPTION', reason=str(ex), input=event)


def dump_event(event):
    if isinstance(event, str):
        return event.encode('utf-8')
    return to_json(event).encode('utf-8')


def make_event(**kwds):
    if 'event' not in kwds:
        raise ValueError('Missing event argument')
    return _make_event(kwds)


def _make_event(obj):
    for key in obj:
        if isinstance(obj[key], dict):
            obj[key] = _make_event(obj[key])
    return Event(obj)
