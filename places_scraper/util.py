import socks
import socket


def init_proxy():
    default_proxy, socket_class = socks.get_default_proxy(), socket.socket

    socks.set_default_proxy(socks.SOCKS5, "localhost", 9150)
    socket.socket = socks.socksocket

    return default_proxy, socket_class

def reset_proxy(settings):
    default_proxy, socket_class = settings

    if default_proxy:
        socks.set_default_proxy(*default_proxy)
    else:
        socks.set_default_proxy(None)
    socket.socket = socket_class
