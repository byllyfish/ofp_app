"""Implements a Datapath class."""

from zof.log import logger
from zof.packet import Packet
from zof.tasklist import TaskList
from zof.exception import RequestError


class Datapath:
    """Reference to a connected datapath.

    Datapath instances are ephemeral. The instance is destroyed when
    the datapath disconnects and a new instance is created when the
    same datapath ID reconnects. Typically, you will never create a
    Datapath instance; an existing one will be passed to you.

    Attributes:
        id (str): Datapath ID
        conn_id (int): Connection Identifier
        closed (bool): True if datapath is closed

    """

    def __init__(self, controller, conn_id, dp_id):
        """Initialize datapath object."""
        self.id = dp_id
        self.conn_id = conn_id
        self.closed = False
        self.zof_driver = controller.zof_driver
        self.zof_tasks = TaskList(controller.zof_loop, controller.on_exception)

    def send(self, msg):
        """Send message to datapath."""
        if self.closed:
            raise RequestError.zof_closed()

        if msg['type'] == 'PACKET_OUT':
            Packet.zof_to_packet_out(msg)

        logger.debug('Send %r dp=%r', msg['type'], self)
        msg['conn_id'] = self.conn_id
        self.zof_driver.send(msg)

    async def request(self, msg):
        """Send message to datapath and wait for reply."""
        if self.closed:
            raise RequestError.zof_closed()

        logger.debug('Send %r dp=%r', msg['type'], self)
        msg['conn_id'] = self.conn_id
        return await self.zof_driver.request(msg)

    def create_task(self, coro):
        """Create managed async task associated with this datapath."""
        self.zof_tasks.create_task(coro)

    def close(self):
        """Close the datapath preemptively."""
        if not self.closed:
            logger.debug('Close dp=%r', self)
            self.closed = True
            self.zof_driver.close_nowait(self.conn_id)
            self.zof_cancel_tasks()

    def zof_cancel_tasks(self):
        """Cancel tasks when datapath disconnects."""
        self.zof_tasks.cancel()

    def __repr__(self):
        """Return string representation of datapath."""
        return '<Datapath conn_id=%d dpid=%s>' % (self.conn_id, self.id)
