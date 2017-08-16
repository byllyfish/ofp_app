from collections import OrderedDict
from .controller import Controller

# Keys for datapath.user_data dictionary. Used by datapath service.
CHANNEL_UP_MSG = '_datapath.channel_up'
FEATURES_MSG = '_datapath.features_reply'
READY_FLAG = '_datapath.ready'


class DatapathList:
    """Represents a collection of datapaths."""

    def __init__(self):
        self._datapaths = OrderedDict()

    def add_datapath(self, *, datapath_id, conn_id):
        """Add datapath to list.

        Implementation is idempotent when arguments are identical.

        Returns:
            Datapath: datapath object
        """
        dpid_key = normalize_datapath_id(datapath_id)
        datapath = self._datapaths.get(dpid_key)
        if datapath is None:
            datapath = Datapath(datapath_id, conn_id)
            self._datapaths[dpid_key] = datapath
        elif datapath.conn_id != conn_id:
            raise ValueError('Datapath already exists: %r' % datapath)
        return datapath

    def delete_datapath(self, *, datapath_id):
        """Remove datapath from list.

        Returns None if datapath is not found.

        Returns:
            Datapath: just removed datapath object (or None)
        """
        dpid_key = normalize_datapath_id(datapath_id)
        datapath = self._datapaths.pop(dpid_key, None)
        return datapath

    def __len__(self):
        return len(self._datapaths)

    def __iter__(self):
        return iter(self._datapaths.values())

    def __getitem__(self, datapath_id):
        dpid_key = normalize_datapath_id(datapath_id)
        return self._datapaths[dpid_key]


class Datapath:
    """Represents a datapath."""

    def __init__(self, datapath_id, conn_id):
        self.datapath_id = datapath_id
        self.conn_id = conn_id
        self.ports = OrderedDict()
        self.up = True
        self.user_data = {}

    def add_port(self, *, port_no):
        """Add port to datapath.

        Implementation is idempotent when arguments are identical.

        Returns:
            Port: port object
        """
        port_no = normalize_port_no(port_no)
        port = self.ports.get(port_no)
        if port is None:
            port = Port(port_no, datapath=self)
            self.ports[port_no] = port
        return port

    def delete_port(self, *, port_no):
        """Remove port from datapath.

        Returns None if port is not found.

        Returns:
            Port: just removed port object (or None)
        """
        port_no = normalize_port_no(port_no)
        port = self.ports.pop(port_no, None)
        return port

    def add_ports(self, port_descs):
        """Add ports from OpenFlow Port descs.

        This is an idempotent operation; it can be used to update existing
        ports from a port_status message.

        Arguments:
            port_descs (List[ObjectView]): list of OpenFlow port desc's.
        """
        for port_desc in port_descs:
            port = self.add_port(port_no=port_desc.port_no)
            port.hw_addr = port_desc.hw_addr
            port.name = port_desc.name
            port.state = port_desc.state
            port.config = port_desc.config

    def close(self):
        """Close connection to datapath; i.e. hang up.

        This function coordinates with the datapath service to make sure no
        apps receive any further events from this datapath.
        """
        assert self.user_data[READY_FLAG]
        self.up = False
        del self.user_data[READY_FLAG]
        Controller.singleton().rpc_call(
            'OFP.CLOSE', ignore_reply=True, conn_id=self.conn_id)

    def __getstate__(self):
        return repr(self)

    def __len__(self):
        return len(self.ports)

    def __bool__(self):
        # Make sure empty datapath is still true.
        return True

    def __iter__(self):
        return iter(self.ports.values())

    def __getitem__(self, port_no):
        port_no = normalize_port_no(port_no)
        return self.ports[port_no]

    def __repr__(self):
        return '<zof.Datapath datapath_id=%s>' % self.datapath_id


class Port:
    """Represents a datapath port."""

    def __init__(self, port_no, datapath):
        self.datapath = datapath
        self.port_no = port_no
        self.hw_addr = None
        self.name = None
        self.state = []
        self.config = []

    def __getstate__(self):
        return repr(self)

    @property
    def datapath_id(self):
        return self.datapath.datapath_id

    @property
    def up(self):
        "Return true if port is up."
        return 'LINK_DOWN' not in self.state

    @property
    def admin_down(self):
        "Return true if port is administratively configured down."
        return 'PORT_DOWN' in self.config

    def __repr__(self):
        return '<zof.Port port_no=%s>' % self.port_no


def normalize_datapath_id(datapath_id):
    """Normalize datapath_id value."""
    if isinstance(datapath_id, int):
        return datapath_id
    if isinstance(datapath_id, str) and datapath_id:
        return int(datapath_id.replace(':', ''), 16)
    raise ValueError('Invalid datapath_id: %r' % datapath_id)


def normalize_port_no(port_no):
    """Normalize port number value to int or string."""
    if isinstance(port_no, int):
        return port_no
    if isinstance(port_no, str):
        try:
            # Convert decimal and hexadecimal port number strings.
            return int(port_no, 0)
        except ValueError:
            return port_no.upper()
    raise ValueError('Invalid port_no: %r' % port_no)
