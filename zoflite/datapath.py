"""Implements a Datapath class."""

import logging
from zoflite.taskset import TaskSet

LOGGER = logging.getLogger(__package__)


class Datapath:
    """Stores info about each connected datapath."""

    def __init__(self, controller, conn_id, event):
        """Initialize datapath object."""
        self.zof_driver = controller.zof_driver
        self.conn_id = conn_id
        self.datapath_id = event['datapath_id']
        self.tasks = TaskSet(controller.zof_loop)

    def send(self, msg):
        """Send message to datapath."""
        LOGGER.debug('Send %r dp=%r', msg['type'], self)

        if msg['type'] == 'PACKET_OUT':
            msg = self.zof_convert_packet_out(msg)

        msg['conn_id'] = self.conn_id
        self.zof_driver.send(msg)

    async def request(self, msg):
        """Send message to datapath and wait for reply."""
        LOGGER.debug('Send %r dp=%r', msg['type'], self)

        msg['conn_id'] = self.conn_id
        return await self.zof_driver.request(msg)

    def create_task(self, coro):
        """Create managed async task associated with this datapath."""
        self.tasks.create_task(coro)

    def zof_cancel_tasks(self):
        """Cancel tasks when datapath disconnects."""
        self.tasks.cancel()

    def zof_convert_packet_in(self, event):
        """Convert incoming packet_in message to a user-friendly format."""
        return event

    def zof_convert_packet_out(self, event):
        """Convert outgoing packet_out from its user-friendly format."""
        return event

    def __repr__(self):
        """Return string representation of datapath."""
        return '<Datapath conn_id=%d dpid=%s>' % (self.conn_id,
                                                  self.datapath_id)
