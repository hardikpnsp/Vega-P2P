from twisted.internet.protocol import Protocol, Factory
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol, TCP4ServerEndpoint
from twisted.internet import reactor
from twisted.protocols import basic
import Node.deserialize as deserialize
from Node.descriptors_pb2 import DescriptorHeader, Ping, Pong, Query, QueryHit
import uuid
connections = []
seenPingID = []


class Gnutella (Protocol):
    # class Gnutella (basic.LineReceiver):
    def __init__(self):
        self.name = "Protocol Object"
        print("protocol init")
        #self.initiator= False
        # if isInitiator:
        #    self.initiator= True

    def connectionMade(self):
        print ("connection recevived")
        
        # add client here

    def setInitializer(self):
        print("self init")
        self.initiator = True

    def dataReceived(self, data):
        # stdout.write(data)
        print("Server received data", data)
        if data == "GNUTELLA CONNECT /0.4 \n\n":
            self.handle_message(data)
        else:
            new_data = deserialize.deserialize(data)
            if new_data.descriptor_header.payload_descriptor == DescriptorHeader.PING:
                self.handle_ping(new_data)
            if new_data.descriptor_header.payload_descriptor == DescriptorHeader.PONG:
                self.handle_pong(new_data)
            if new_data.descriptor_header.payload_descriptor == DescriptorHeader.QUERY:
                self.handle_query(new_data)
            if new_data.descriptor_header.payload_descriptor == DescriptorHeader.QUERYHIT:
                self.handle_queryhit(new_data)

    def handle_message(self, data):
        # handle the gnutella connect and gnutella ok here
        print("appending connection ", self)
        connections.append(self)
        peer = self.transport.getPeer()
        print("Connected to {0}:{1}".format(peer.host, peer.port))
        self.transport.write("Gnutella OK \n\n".encode('utf-8'))

    def send_ping(self, ping):
        #send ping to all connections except self 
        #save the ping id for later use 
        # do we remove the ping id based on time ?  
        if ping.descriptor_header.ttl <= 0:
            return
        p = ping.SerializeToString()
        print("Sending ping")
        for cn in connections:
            if cn != self:
                cn.transport.write(p.encode('utf-8'))  

    def handle_ping(self, ping):
        # append the ping id to seen array 
        # add some time logic to updating the array 
        # create and send the pong for ping
        # forward the ping to other nodes

        print("handling ping")
        seenPingID.append(ping.descriptor_header.descriptor_id)
        ping.descriptor_header.ttl -= 1
        ping.descriptor_header.hops += 1
        self.send_ping(ping)
        self.send_pong(ping)

    def send_pong(self, ping):
        # this method creates first pong
        # number of files and size to be calculated and added later
        pong = Pong()
        pong.descriptor_header.descriptor_id = ping.descriptor_header.descriptor_id
        pong.descriptor_header.ttl = 7
        pong.descriptor_header.hops = 0
        pong.descriptor_header.payload_descriptor = DescriptorHeader.PONG
        pong.descriptor_header.payload_length = 14
        pong.port = self.transport.getHost().port
        pong.ip_address = self.transport.getHost().host
        pong.no_of_files_shared = 5
        pong.no_of_kb_shared = 1000
        print("pong created")
        p = pong.SerializeToString()
        for cn in connections:
            cn.transport.write(p.encode('utf-8'))  # send p object here
    
    def handle_pong(self, pong):
        #check if the same ping id has been recieved by this node. 
        # if so 
        #   forward the pong to all the connections except self
        #   ttl --
        #   hops ++ 
        # else 
        #   discard this pong 
        self.status = "incomplete"
    
    def handle_query(self, query):
        self.status = "incomplete"
    
    def handle_queryhit(self, queryhit):
        self.status = "incomplete"


class GnutellaFactory (Factory):
    def __init__(self, isInitializer=False):
        print("factory init")
        self.initializer = False
        if isInitializer:
            self.initializer = True

    def buildProtocol(self, addr):
        print("protocol built")
        prot = Gnutella()
        if self.initializer:
            prot.setInitializer()
        return prot

    def startedConnecting(self, connector):
        print("Trying to connect")

    def clientConnectionFailed(self, transport, reason):
        print("Client conneciton lost")


if __name__ == "__main__":
    server = GnutellaFactory()
    usedport = reactor.listenTCP(8000, server)
    reactor.run()
