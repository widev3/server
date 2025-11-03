from abc import ABC, abstractmethod


class Mount(ABC):
    @abstractmethod
    def get_location(self):
        raise NotImplementedError

    @abstractmethod
    def get_target(self):
        raise NotImplementedError

    @abstractmethod
    def get_offset(self):
        raise NotImplementedError

    @abstractmethod
    def get_position(self):
        raise NotImplementedError

    @abstractmethod
    def get_behavior(self):
        raise NotImplementedError

    @abstractmethod
    def get_running(self):
        raise NotImplementedError

    @abstractmethod
    def set_location(self, location):
        raise NotImplementedError

    @abstractmethod
    def set_target(self, alt=None, az=None, ra=None, dec=None) -> None:
        raise NotImplementedError

    @abstractmethod
    def set_absolute_offset(self, alt=None, az=None, ra=None, dec=None) -> None:
        raise NotImplementedError

    @abstractmethod
    def set_relative_offset(self, alt=None, az=None, ra=None, dec=None) -> None:
        raise NotImplementedError

    @abstractmethod
    def run(self, bh: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError
