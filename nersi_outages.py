from application.graph.network_rsi import LMPFactory
        
        

if __name__ == "__main__":

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