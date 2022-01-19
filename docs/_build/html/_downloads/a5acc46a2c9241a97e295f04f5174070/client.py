import socket, time

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("localhost", 5002))
time.sleep(1)
print("sending msg")
sock.send("kokkelis".encode("ascii"))
time.sleep(1)
print("sending msg2")
sock.send("kokkelis2".encode("ascii"))
time.sleep(1)
print("closing socket")
# sock.shutdown()
sock.close()
