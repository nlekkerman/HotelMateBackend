import ssl
import socket

hostname = "ec2-54-228-126-241.eu-west-1.compute.amazonaws.com"
port = 12630

context = ssl._create_unverified_context()

with socket.create_connection((hostname, port)) as sock:
    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
        # Get the raw DER-encoded certificate
        der_cert = ssock.getpeercert(True)
        print(f"Raw DER cert bytes length: {len(der_cert)}")

        # You can save this cert to a file if you want to inspect it later
        with open("redis_cert.der", "wb") as f:
            f.write(der_cert)

        # Also try to get the full cert chain if supported
        if hasattr(ssock, "get_verified_chain"):
            chain = ssock.get_verified_chain()
            print(f"Cert chain length: {len(chain)}")
        else:
            print("No method to get full cert chain on this Python version.")
