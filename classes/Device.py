from abc import ABC, abstractmethod


class Device(ABC):
    def read(self, *args) -> list:
        raise NotImplementedError

    def write(self, *args) -> list:
        raise NotImplementedError
