from packet import Packet
import util

class FrgHandler:

    def __init__(self):
        self.frgState="complete"

    def formPacket(self, datagram):
        
        pack = util.unpackMsg(datagram)
        formedPackTemp=Packet(pack.frg, pack.ack,
                                    pack.msgType,
                                    pack.roomType,
                                    pack.seqNum, pack.userId,
                                    pack.destId, length=0, data=None)
        formedPack=formedPackTemp                            
        if pack.frg==0 and self.frgState=="complete":
            return pack
        elif pack.frg==0 and self.frgState=="waitForNextFrg":
            formedPack.length+=pack.length
            formedPack.data+=pack.data
            return formedPack
        
        if pack.frg==1:
            self.frgState=="waitForNextFrg"
            formedPack.length+=pack.length
            formedPack.data+=pack.data
            return None 
    
