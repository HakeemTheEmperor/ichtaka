class AppException(Exception):
    message: str = "Application error"
    status_code:int = 400
    code:str = "APP_ERROR"
    
    def __init__(self, message: str | None = None):
        if message is not None:
            self.message = message
        super().__init__(self.message)
    