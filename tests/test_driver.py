import pytest
from zoflite.driver import Driver
from zoflite.exception import RequestError

# Max size of RPC message supported by oftr.
MSG_LIMIT = 2**20 - 1


@pytest.mark.asyncio
async def test_request_error():
    """Test exception creation."""
    event = {'abc': 1}
    exc = RequestError(event)
    assert str(exc) == "Other event: {'abc': 1}"
    assert exc.event is event


@pytest.mark.asyncio
async def test_driver_request():
    """Driver context manager's request api."""

    async with Driver(debug=True) as driver:
        assert driver.pid >= 0

        request = {'id': 1, 'method': 'OFP.DESCRIPTION'}
        reply = await driver.request(request)

        assert request == {
            'id': 1,
            'method': 'OFP.DESCRIPTION'
        }, 'Request modified'
        assert reply['api_version'] == '0.9'
        assert reply['sw_desc'].startswith('0.')
        assert reply['versions'] == list(range(1, 7))

        with pytest.raises(RequestError) as excinfo:
            request = {'method': 'OFP.SEND', 'params': {'xid': 123}}
            await driver.request(request)

        assert "missing required key 'type'" in str(excinfo.value)
        assert driver.event_queue.empty()


@pytest.mark.asyncio
async def test_driver_not_reentrant():
    """Driver context manager is not re-entrant."""

    driver = Driver()
    async with driver:
        with pytest.raises(AssertionError):
            async with driver:
                pass


@pytest.mark.asyncio
async def test_driver_nonexistant_method():
    """Non-existant JSON-RPC method."""

    async with Driver() as driver:
        request = {'id': 1, 'method': 'NON_EXISTANT'}
        with pytest.raises(RequestError) as excinfo:
            await driver.request(request)
        assert 'unknown method' in str(excinfo.value)
        assert driver.event_queue.empty()


@pytest.mark.asyncio
async def test_driver_invalid_rpc():
    """Non-existant JSON-RPC method."""

    async with Driver() as driver:
        request = {'id': 1, 'meth': 'INVALID'}
        with pytest.raises(RequestError) as excinfo:
            await driver.request(request)
        assert "missing required key 'method'" in str(excinfo.value)
        assert driver.event_queue.empty()


@pytest.mark.asyncio
async def test_large_rpc_too_big():
    """Large RPC payload (too big)."""

    async with Driver() as driver:
        request = {'id': 1, 'method': 'FOO', 'params': 'x' * MSG_LIMIT}
        with pytest.raises(RequestError) as excinfo:
            await driver.request(request)

        # The reply error should be a closed error.
        assert 'connection closed' in str(excinfo.value)
        assert driver.event_queue.empty()


@pytest.mark.asyncio
async def test_large_rpc():
    """Large RPC payload (big, but not too big)."""

    async with Driver() as driver:
        request = {'id': 1, 'method': 'FOO', 'params': 'x' * (MSG_LIMIT - 100)}
        with pytest.raises(RequestError) as excinfo:
            await driver.request(request)

        assert 'unknown method' in str(excinfo.value)
        assert driver.event_queue.empty()


@pytest.mark.asyncio
async def _driver_request_benchmark(name, loops):
    """Benchmark making async requests."""

    from timeit import default_timer as _timer

    async def _test(loops):
        DESC = {'id': 1, 'method': 'OFP.DESCRIPTION'}
        async with Driver() as driver:
            start_time = _timer()
            for _ in range(loops):
                await driver.request(DESC)
            return _timer() - start_time

    bench = {'benchmark': name, 'loops': loops, 'times': []}

    for _ in range(4):
        bench['times'].append(await _test(bench['loops']))

    return bench


@pytest.mark.asyncio
async def test_driver_request_benchmark():
    """Benchmark making async requests."""

    print(await _driver_request_benchmark('driver_request', 1000))


@pytest.mark.asyncio
async def test_driver_openflow():
    """Connect agent driver to controller driver."""

    def _iter(queue):
        for _ in range(queue.qsize()):
            yield queue.get_nowait()

    def _events(queue):
        return [event['type'] for event in _iter(queue)]

    async with Driver() as controller:
        # Start controller listening on a port.
        await controller.listen('6653')

        async with Driver() as agent:
            # Agent connects to controller.
            conn_id = await agent.connect('127.0.0.1:6653')
            agent.send(dict(type='BARRIER_REPLY', conn_id=conn_id))
            await agent.close(conn_id)

    agent_log = _events(agent.event_queue)
    controller_log = _events(controller.event_queue)

    assert controller_log == ['CHANNEL_UP', 'BARRIER_REPLY', 'CHANNEL_DOWN']
    assert agent_log == ['CHANNEL_UP', 'CHANNEL_DOWN']
