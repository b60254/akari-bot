from typing import Union

from tenacity import retry, stop_after_attempt

from core.elements import MessageSession
from database import session, auto_rollback_error
from .orm import CytoidBindInfo


class CytoidBindInfoManager:
    @retry(stop=stop_after_attempt(3), reraise=True)
    @auto_rollback_error
    def __init__(self, msg: MessageSession):
        self.targetId = msg.target.senderId
        self.query = session.query(CytoidBindInfo).filter_by(targetId=self.targetId).first()
        if self.query is None:
            session.add_all([CytoidBindInfo(targetId=self.targetId, username='')])
            session.commit()
            self.query = session.query(CytoidBindInfo).filter_by(targetId=self.targetId).first()

    @retry(stop=stop_after_attempt(3), reraise=True)
    @auto_rollback_error
    def get_bind_username(self) -> Union[str, None]:
        bind_info = self.query.username
        if bind_info != '':
            return bind_info
        return None

    @retry(stop=stop_after_attempt(3), reraise=True)
    @auto_rollback_error
    def set_bind_info(self, username):
        self.query.username = username
        session.commit()
        return True

    @retry(stop=stop_after_attempt(3), reraise=True)
    @auto_rollback_error
    def remove_bind_info(self):
        session.delete(self.query)
        session.commit()
        return True
