import math
import time
from simulator.node import Node
import json
import copy

class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.cost = {}
        self.dist_matrix = {}
        self.node_matrix = {}
        self.adjacent = []
        self.visited_nodes = []
        self.latency_val = -1

    # Return a string
    def __str__(self):
        return "Rewrite this function to define your node dump printout"

    # Fill in this function
    def getDC(self, val):
        return copy.deepcopy(val)

    def getJsonDump(self, msg):
        return json.dumps(msg)

    def getJson(self, msg):
        return json.loads(msg)

    def getPresent(self, val, container):
        if val in container:
            return True
        return False

    def getNotPresent(self, val, container):
        if val not in container:
            return True
        return False

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        hop = self.dist_matrix[destination][1]
        while hop not in self.adjacent:
            if hop is None:
                return None
            print(f"hop: {hop}")
            print(f"dist_matrix: {self.dist_matrix}")
            hop = self.dist_matrix[hop][1]
        return hop      

    def link_has_been_updated(self, neighbor, latency):
        if latency == self.latency_val:
            del self.cost[neighbor]
            lst = []
            self.dist_matrix[neighbor] = [math.inf, None, lst]
            self.adjacent.remove(neighbor)
            self.update_dist_vec()
            mess = self.getJsonDump([self.id, self.dist_matrix])
            for n in self.adjacent:
                self.send_to_neighbor(n, mess)
            time.sleep(1)
            return

        if self.getNotPresent(self.id, self.visited_nodes):
            self.dist_matrix[self.id] = [0, self.id, [self.id]]
            self.visited_nodes.append(self.id)
        
        if self.getNotPresent(neighbor, self.adjacent):
            self.adjacent.append(neighbor)
            self.visited_nodes.append(neighbor)

        self.cost[neighbor] = latency
        self.dist_matrix[neighbor] = [latency, neighbor, [neighbor]]
        copyVec = self.getDC(self.dist_matrix)

        mess = self.getJsonDump([self.id, self.dist_matrix])
        for n in self.adjacent:
            self.send_to_neighbor(n, mess)

    # Fill in this function
    def process_incoming_routing_message(self, m):
        mess = self.getJson(m)
        sender, recvDistVec = mess[0], mess[1]

        newbie = {}
        for item in recvDistVec:
            newbie[int(item)] = recvDistVec[item]
        if self.getPresent(sender, self.adjacent):
            self.node_matrix[sender] = newbie
        
        for nvec in self.node_matrix:
            for val in self.node_matrix[nvec]:
                if self.getNotPresent(int(val), self.visited_nodes):
                    self.visited_nodes.append(int(val))
        copyVec = self.getDC(self.dist_matrix)
        self.update_dist_vec()
        if self.dist_matrix != copyVec:
            for n in self.adjacent:
                mess = self.getJsonDump([self.id, self.dist_matrix])
                self.send_to_neighbor(n, mess)

    def update_dist_vec(self):
        for item in self.visited_nodes:
            if item != self.id:
                min = math.inf
                minHop = None
                for n in self.cost:
                    if self.getPresent(n, self.node_matrix) and self.getPresent(item, self.node_matrix[n]):
                        if self.cost[n] + self.node_matrix[n][item][0] < min:
                            if self.node_matrix[n][item][2]:
                                if self.getNotPresent(self.id, self.node_matrix[n][item][2]):
                                    min = self.cost[n] + self.node_matrix[n][item][0]
                                    minHop = n
                            else:
                                min = self.cost[n] + self.node_matrix[n][item][0]
                                minHop = n
                                
                if min != math.inf and minHop != None:
                    if not self.node_matrix[minHop][item][2]:
                        self.dist_matrix[item] = [min, minHop, [minHop]]
                    else:
                        temp = self.getDC(self.node_matrix[minHop][item][2])
                        temp.append(minHop)
                        temp.append(self.id)
                        self.dist_matrix[item] = [min, minHop, temp]


class destination():
    def __init__(self, _cost, _next_hop):
        self.latency = _cost
        self.next_hop = _next_hop