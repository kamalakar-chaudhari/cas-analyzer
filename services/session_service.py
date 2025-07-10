class SessionService:
    def __init__(self):
        self.sessions = dict()

    def set_session_data(self, session_id, value):
        self.sessions[session_id] = value

    def get_session_data(self, session_id):
        return self.sessions.get(session_id, {})
