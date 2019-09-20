import networkx as nx
from networkx.algorithms.flow.maxflow import maximum_flow
import matplotlib.pyplot as plt


class LMPGraph():
    def __init__(self):
        self.G = nx.DiGraph()
        self.transmission = {}
        self.constraints = {}

    def add_node(self, node_label):
        """
        Adds a trading node (ie location in a locational marginal pricing market).
        """
        self.G.add_node(node_label)
    
    def set_transmission(self, from_node, to_node, capacity, label):
        """
            Adds unidirectional transmission between two nodes, at a certain capacity (MW)
            Label must be unique. 
        """
        key = from_node+'-'+to_node
        self.transmission[key] = {} if key not in self.transmission else self.transmission[key]
        self.transmission[key][label] = {'from_node':from_node, 'to_node': to_node, 'label':label, 'capacity':int(capacity)}
        total = sum([self.transmission[key][label]['capacity'] for label in self.transmission[key] ])
        self.G.add_edge(from_node,to_node,capacity=int(total))
    
    def set_constraint(self, from_node, to_node, capacity_reduction, label):
        key = from_node+'-'+to_node
        self.constraints[key] = {} if key not in self.constraints else self.constraints[key]
        self.constraints[key][label] = {'from_node':from_node, 'to_node': to_node, 'label':label, 'capacity_reduction':int(capacity_reduction)}
    
    def get_transmission(self):
        return self.transmission

    def calculate_flow(self, to_node, spare_capacities):
        # Add a consolidated source node to all nodes with spare capacities. 
        self.G.add_node('Consolidated Source')
        for node in spare_capacities:
            self.G.add_edge('Consolidated Source', node, capacity=int(spare_capacities[node]))
        
        flow_value, flow_dict = maximum_flow(self.G, 'Consolidated Source', to_node)

        # Cleaning Up - Remove the consolidated source node.
        self.G.remove_node('Consolidated Source')
        return flow_value
        
    def print(self):
        print("Edges:")
        for e in self.G.edges:
            print(e, self.G.edges[e])
        

    def draw(self):
        
        nx.draw(self.G)
        plt.show()

class LMPFactory():
    def get_australian_nem(self):
        market = LMPGraph()

        market.add_node('NSW')
        market.add_node('VIC')
        market.add_node('SA')
        market.add_node('QLD')
        market.add_node('TAS')

        market.set_transmission('NSW', 'QLD', 107, "Terranora NSW->QLD")
        market.set_transmission('QLD', 'NSW', 210, "Terranora QLD->NSW")
        market.set_transmission('NSW', 'QLD', 600, "Queensland NSW Interconnector NSW->QLD")
        market.set_transmission('QLD', 'NSW', 1078, "Queensland NSW Interconnector QLD->NSW")
        market.set_transmission('VIC', 'NSW', 1600, "Victoria to NSW Interconnector VIC->NSW")
        market.set_transmission('NSW', 'VIC', 1350, "Victoria to NSW Interconnector NSW->VIC")
        market.set_transmission('TAS', 'VIC', 594, "Basslink TAS->VIC")
        market.set_transmission('VIC', 'TAS', 478, "Basslink VIC->TAS")
        market.set_transmission('VIC', 'SA', 600, "Heywood Interconnector VIC->SA")
        market.set_transmission('SA', 'VIC', 500, "Heywood Interconnector SA->VIC")
        market.set_transmission('VIC', 'SA', 220, "Murraylink VIC->SA")
        market.set_transmission('SA', 'VIC', 200, "Murraylink SA->VIC")
        return market

if __name__ == "__main__":
    # Interconnector capacities below taken as maximums in 'INTERCONNECTOR CAPABILITIES FOR THE NATIONAL ELECTRICITY MARKET' (2017) https://www.aemo.com.au/-/media/Files/Electricity/NEM/Security_and_Reliability/Congestion-Information/2017/Interconnector-Capabilities.pdf
    market = LMPFactory().get_australian_nem()
    
    # I think these need to be netted internally - seems to only support one edge between two nodes. 
    flow = market.calculate_flow('SA', {'VIC': 100, 'NSW': 50, 'QLD': 600} )
    print(flow)

    # market.draw()
    market.print()


# Breadth first search. Start with the closest nodes. Calc maximum flow at their max avail. Constrain closest lines as per flow. Repeat. 

# This is NEARLY the maximum flow algorithm with multiple sources and one sink. 
# To do this you add a consolidated source connected to each node, with constraints at the required node residual capacities. 
# YES. Solved. 