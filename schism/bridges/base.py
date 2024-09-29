class BridgeClient:
    ...


class BridgeServer:
    ...


class BaseBridge:
    @classmethod
    def create_client(cls) -> BridgeClient:
        raise NotImplementedError

    @classmethod
    def create_server(cls) -> BridgeServer:
        raise NotImplementedError