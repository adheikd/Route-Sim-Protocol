import math
import time
import random

from simulator.node import Node
import json
import copy
import uuid

class Link_State_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.routeTable = {}
        self.price_map = {}
        self.recentlySeenSeq = {}
        self.D = {}
        self.latencyThresh = -1

    def __str__(self):
        return "ID:" + str(self.id)

    def getMessage(self, msg):
        val = json.loads(msg)
        return val

    def getMessageList(self, msg):
        lst = []
        for i in range(0, 5):
            lst.append(msg[i])
        return lst

    def getJsonDump(self, msg):
        return json.dumps(msg)

    def getMin(self, val1, val2):
        if val1 > val2:
            return val2
        return val1

    def getFS(self, val1, val2):
        return frozenset([val1, val2])

    def getDC(self, val):
        return copy.deepcopy(val)

    def dijkstra(self):
        dist = {}
        nodes = [self.id]
        for keys in self.price_map:
            key_list = list(keys)
            tup = [math.inf, None]
            if self.id not in key_list:
                if key_list[0] not in list(dist.keys()):
                    dist[key_list[0]] = tup
                    continue
                if key_list[1] not in list(dist.keys()):
                    dist[key_list[1]] = tup
            else:
                src = key_list[0] if key_list[0] == self.id else key_list[1]
                dst = key_list[1] if key_list[0] == self.id else key_list[0]
                dist[dst] = [self.price_map[keys][0], self.id]  
                
        while len(nodes) < len(self.price_map):
            minimum = float('inf')
            for val in dist:
                w = val if dist[val][0] < minimum and val not in nodes else w
                minimum = dist[val][0] if dist[val][0] < minimum and val not in nodes else minimum
            nodes.append(w)
            for keys in self.price_map:
                key_list = list(keys)
                if w in key_list:
                    src = key_list[0] if key_list[0] == w else key_list[1]
                    dst = key_list[1] if key_list[0] == w else key_list[0]
                    if dst == self.id:
                        continue
                    chk = self.getDC(dist[dst][0])
                    sum_ = dist[w][0] + self.price_map[keys][0]
                    dist[dst][0] = self.getMin(sum_, dist[dst][0])
                    dist[dst][1] = src if dist[dst][0] != chk else dist[dst][1]
        return dist

    def link_has_been_updated(self, neighbor, latency):
        if latency == self.latencyThresh:
            self.neighbors.remove(neighbor)
            key = self.getFS(self.id, neighbor)
            seq = self.price_map[key][1]
            del self.price_map[key]
            message = self.getJsonDump([self.id, neighbor, latency, seq+1, self.id])
            self.send_to_neighbors(message)
            return
            
        if neighbor not in self.neighbors:
            self.neighbors.append(neighbor)
            for key in self.price_map:
                lKey = list(key)
                message = [lKey[0], lKey[1], self.price_map[key][0], self.price_map[key][1], self.id]
                message = self.getJsonDump(message)
                self.send_to_neighbor(neighbor, message)
        if self.getFS(self.id, neighbor) in self.price_map:
            seq = self.price_map[self.getFS(self.id, neighbor)][1]
            seq += 1
        else:
            seq = 0
        self.price_map[self.getFS(self.id, neighbor)] = [latency, seq]
        message = [self.id, neighbor, latency, seq, self.id]
        message = self.getJsonDump(message)
        for idx, n in enumerate(self.neighbors):
            self.send_to_neighbor(n, message)

    def process_incoming_routing_message(self, m):
        msg = self.getMessage(m)
        msg_lst = self.getMessageList(msg)
        src, dst, cost, seq, initial = msg_lst[0], msg_lst[1], msg_lst[2], msg_lst[3], msg_lst[4]
        srcDstFS = self.getFS(src, dst)
        if cost == -1:
            message = [msg[0], msg[1], msg[2], msg[3], self.id]
            message = self.getJsonDump(message)
            if(self.price_map.pop(srcDstFS, None)):
                for idx, n in enumerate(self.neighbors):
                    if n != initial:
                        self.send_to_neighbor(n, message)
            return
        seq2 = self.price_map[srcDstFS][1] if srcDstFS in self.price_map else seq
        if srcDstFS in self.price_map:
            seq2 = self.price_map[srcDstFS][1]
            if seq2 < seq:
                key = srcDstFS
                self.price_map[key] = [cost, seq]
                message = [src, dst, cost, seq, self.id]
                message = self.getJsonDump(message)
                for idx, n in enumerate(self.neighbors):
                    if n != initial:
                        self.send_to_neighbor(n, message)
            elif seq2 > seq:
                message = [src, dst, cost, seq2, self.id]
                message = self.getJsonDump(message)
                self.send_to_neighbor(initial, message)
        else:
            key = srcDstFS
            self.price_map[key] = [cost, seq2]
            message = [src, dst, cost, seq2, self.id]
            message = self.getJsonDump(message)
            for idx, n in enumerate(self.neighbors):
                if n != initial:
                    self.send_to_neighbor(n, message)

    def get_next_hop(self, dstination):
        self.dist = self.dijkstra()
        currPrev = self.dist[dstination][1]
        if currPrev == self.id:
            return dstination
        nextPrev = self.dist[currPrev][1]
        while True:
            if nextPrev == self.id:
                break
            currPrev = nextPrev
            nextPrev = self.dist[currPrev][1]
        return currPrev
