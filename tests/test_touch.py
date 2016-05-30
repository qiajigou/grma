def test_touch():
    from client import get_client
    client = get_client()
    resp = client.hello('hello')
    assert 'hello' in str(resp)
