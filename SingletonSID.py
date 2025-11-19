class SingletonSID:
    _instance = None
    SID = None
    DEVICE_ID = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SingletonSID, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        super().__init__()

        self._initialized = True
        self.SID = None
        self.DEVICE_ID = None

    def set_SID(self, sid):
        self.SID = sid
