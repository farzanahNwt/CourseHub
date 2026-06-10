import xmlrpc.client

SERVER_IP = '192.168.1.100'
SERVER_PORT = 5001

try:
    proxy = xmlrpc.client.ServerProxy(f"http://{SERVER_IP}:{SERVER_PORT}")
    
    result = proxy.ViewCourse("CS101")
    print(f"Course details: {result}")
    
    register_result = proxy.RegisterCourse("student123", "CS101")
    print(f"Registration: {register_result}")
    
except ConnectionRefusedError:
    print(f"❌ Cannot connect to {SERVER_IP}:{SERVER_PORT}")
    print("   Check: 1) Server is running? 2) IP is correct? 3) Firewall?")
except Exception as e:
    print(f"❌ Error: {e}")
