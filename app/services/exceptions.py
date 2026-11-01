class StorageInternalException(Exception):

    def __init__(self, message="Internal storage error."):
        self.message = message
        super().__init__(self.message)
