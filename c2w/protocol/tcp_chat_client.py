# -*- coding: utf-8 -*-
from twisted.internet.protocol import Protocol
import logging
from twisted.internet import reactor
import util
import struct
from config import attempt_num, timeout
from c2w.main.constants import ROOM_IDS
from packet import Packet
from tables import type_code, type_decode, state_code
from tables import error_decode, state_decode, room_type, room_type_decode

logging.basicConfig()
moduleLogger = logging.getLogger('c2w.protocol.tcp_chat_client_protocol')


class c2wTcpChatClientProtocol(Protocol):

    def __init__(self, clientProxy, serverAddress, serverPort):
        """
        :param clientProxy: The clientProxy, which the protocol must use
            to interact with the Graphical User Interface.
        :param serverAddress: The IP address (or the name) of the c2w server,
            given by the user.
        :param serverPort: The port number used by the c2w server,
            given by the user.

        Class implementing the UDP version of the client protocol.

        .. note::
            You must write the implementation of this class.

        Each instance must have at least the following attribute:

        .. attribute:: clientProxy

            The clientProxy, which the protocol must use
            to interact with the Graphical User Interface.

        .. attribute:: serverAddress

            The IP address (or the name) of the c2w server.

        .. attribute:: serverPort

            The port number used by the c2w server.

        .. note::
            You must add attributes and methods to this class in order
            to have a working and complete implementation of the c2w
            protocol.
        """
        self.serverAddress = serverAddress
        self.serverPort = serverPort
        self.clientProxy = clientProxy
        self.headFound = False
        self.currentHead = ""  # current header in binary mode
        self.currentSize = 0
        self.buf = ""
        self.header = Packet(0, 0, 0, 3, 0, 0, 0, 0, None)

        self.seqNum = 0  # sequence number for the next packet to be sent
        self.serverSeqNum = 0  # sequence number of the next not ack packet
        self.userId = 0
        self.userName = ""
        self.packReceived = False
        self.movieList = []
        self.users = []  # userId: user
        self.state = state_code["disconnected"]
        self.movieRoomId = -1  # not in movie room
        self.currentMovieIp = None
        self.currentMoviePort = None
        self.currentMovieRoom = None

    def sendPacket(self, packet, callCount=0):
        """
        param packet: Packet object
        param callCount: only used for the timeout mechanism.
        """
        # the packet is received

        if packet.ack == 1:
            print "###sending ACK packet###:", packet
            buf = util.packMsg(packet)
            self.transport.write(buf)
            return

        if packet.seqNum != self.seqNum:
            return

        print "###sending packet###:", packet
        buf = util.packMsg(packet)
        self.transport.write(buf)
        callCount += 1
        if callCount < attempt_num:
            reactor.callLater(timeout, self.sendPacket, packet, callCount)
        else:
            print "too many tries, packet:", packet," aborted"
            return

    def sendLoginRequestOIE(self, userName):
        """
        :param string userName: The user name that the user has typed.

        The controller calls this function as soon as the user clicks on
        the login button.
        """
        moduleLogger.debug('loginRequest called with username=%s', userName)
        self.roomType = 3
        self.seqNum = 0  # reset seqNum
        self.userId = 0  # use reserved userId when login
        self.userName = userName

        loginRequest = Packet(frg=0, ack=0, msgType=0,
                    roomType=self.roomType, seqNum=self.seqNum,
                    userId=self.userId, destId=0, length=len(userName),
                    data=userName)
        self.sendPacket(loginRequest)
        self.state = state_code["loginWaitForAck"]

    def sendChatMessageOIE(self, message):
        """
        :param message: The text of the chat message.
        :type message: string

        Called **by the controller**  when the user has decided to send
        a chat message

        .. note::
           This is the only function handling chat messages, irrespective
           of the room where the user is.  Therefore it is up to the
           c2wChatClientProctocol or to the server to make sure that this
           message is handled properly, i.e., it is shown only by the
           client(s) who are in the same room.
        """
        pass

    def sendJoinRoomRequestOIE(self, roomName):
        """
        :param roomName: The room name (or movie title.)

        Called **by the controller**  when the user
        has clicked on the watch button or the leave button,
        indicating that she/he wants to change room.

        .. warning:
            The controller sets roomName to
            c2w.main.constants.ROOM_IDS.MAIN_ROOM when the user
            wants to go back to the main room.
        """
        pass

    def sendLeaveSystemRequestOIE(self):
        """
        Called **by the controller**  when the user
        has clicked on the leave button in the main room.
        """
        pass

    def extractPackets(self, data):
        """
        return: a list of packet objects
        """
        packList = []
        while data != "":
            # header detected
            if not self.headFound:
                print "PACKET HEADER DETECTED"
                remainHeadLength = 6 - len(self.currentHead)
                if len(data) >= remainHeadLength:
                    if self.currentHead != "":
                        self.currentHead += data[0:remainHeadLength]
                        data = data[remainHeadLength:]
                    else:
                        self.currentHead = data[0:6]
                        data = data[6:]
                    self.header = util.unpackHeader(self.currentHead)
                    self.buf += self.currentHead
                    self.currentHead = ""
                    self.headFound = True
                else:
                    self.currentHead += data

            # remain msg in the packet
            else:
                # The packet is separated into many TCP packets
                if len(data) <= (self.header.length - self.currentSize):
                    self.buf += data
                    self.currentSize += len(data)
                    data = ""
                # Multiple packets are packed into one TCP packet, always happen
                else:  # cut the data
                    t_data = data[0:self.header.length - self.currentSize]
                    self.buf += t_data
                    self.currentSize += len(t_data)
                    data = data[self.header.length - self.currentSize:]

            if self.currentSize >= self.header.length and self.headFound:
                packList.append(util.unpackMsg(self.buf))
                self.headFound = False
                self.currentSize = 0
        return packList

    def dataReceived(self, data):
        """
        :param data: The message received from the server
        :type data: A string of indeterminate length

        Twisted calls this method whenever new data is received on this
        connection.
        """
        print "#### data received!"
        packList = self.extractPackets(data)

        for pack in packList:
            print "## packet received:", pack
            # TODO
            pass
        pass
