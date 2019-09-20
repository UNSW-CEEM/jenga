from prettytable import PrettyTable
from . import config


class TableManager():
    def __init__(self):
        self.tables = {}
        self.field_names = {}

    def add_row(self, table_name, row):
        """Takes a table name and a list of items to go in a row. """
        self.tables[table_name] = [] if table_name not in self.tables else self.tables[table_name]
        self.tables[table_name].append(row)
    
    def set_field_names(self,table_name, filed_names ):
        """Takes a table name and a list of field names."""
        self.field_names[table_name] = filed_names

    def print_tables(self):
        """Pretty-prints all the tables to terminal."""
        for table_name in self.tables:
            pt = PrettyTable()
            pt.field_names = self.field_names[table_name] if table_name in self.field_names else []
            for row in self.tables[table_name]:
                pt.add_row(row)
            print(pt)

    def export_tables_to_csv(self):
        """Puts all the tables in one big csv."""
        with open(config.CSV_FILENAME, 'w') as f:
            for table_name in self.tables:
                lines = [
                    "\n",
                    table_name,
                    "\n",
                    ', '.join(self.field_names[table_name]) if table_name in self.field_names else ""
                    "\n",
                    "\n",
                ]
                for row in self.tables[table_name]:
                    lines.append(', '.join([str(x) for x in row])) 
                    lines.append("\n")

                f.writelines(lines)

        

def get_hhi_stat_table(table_manager, timeseries):
    """Extracts a number of metrics related to HHI"""

    table_manager.set_field_names('hhi',["Metric","Label", "Value"])

    MODERATELY_CONCENTRATED = 1500
    HIGHLY_CONCENTRATED = 2500
    total_count = {}
    moderately = {}
    highly = {}
    for t in timeseries:
        for key in timeseries[t]:
            if 'hhi_' in key:
                total_count[key] = 1 if key not in total_count else total_count[key] + 1
                moderately[key] = 0 if key not in moderately else moderately[key]
                highly[key] = 0 if key not in highly else highly[key]
                if timeseries[t][key] > HIGHLY_CONCENTRATED:
                    highly[key] += 1
                elif timeseries[t][key] > MODERATELY_CONCENTRATED:
                    moderately[key] += 1
    
    for key in total_count:
        table_manager.add_row('hhi',[key, "% Highly", 100.0 * float(highly[key])/ float(total_count[key])])
        table_manager.add_row('hhi',[key, "% Moderately", 100.0 * float(moderately[key])/ float(total_count[key])])
        # table.add_row([key, "Count Moderately", moderately[key]])
        # table.add_row([key, "Count Highly", highly[key]])
        # table.add_row([key, "Count Total", total_count[key] ])
        



def get_entropy_stat_table(table_manager, timeseries):
    """Extracts a number of metrics related to entropy"""

   
    table_manager.set_field_names('entropy',["Metric","Label", "Value"])

    THRESHOLD = 3.32
    HIGHLY_CONCENTRATED = 2500
    total_count = {}
    concentrated = {}
    
    for t in timeseries:
        for key in timeseries[t]:
            if 'entropy_' in key:
                total_count[key] = 1 if key not in total_count else total_count[key] + 1
                concentrated[key] = 0 if key not in concentrated else concentrated[key]
                if timeseries[t][key] < THRESHOLD:
                    concentrated[key] += 1
    
    for key in total_count:
        table_manager.add_row('entropy',[key, "% Concentrated", 100.0 * float(concentrated[key])/ float(total_count[key])])


def get_four_firm_stat_table(table_manager, timeseries):
    """Extracts a number of metrics related to 4-Firm Concn Ratio"""

    table_manager.set_field_names('four_firm',["Metric","Label", "Value"] )

    MODERATELY_CONCENTRATED = 50
    HIGHLY_CONCENTRATED = 0.8
    total_count = {}
    moderately = {}
    highly = {}
    for t in timeseries:
        for key in timeseries[t]:
            if 'four_firm' in key:
                total_count[key] = 1 if key not in total_count else total_count[key] + 1
                moderately[key] = 0 if key not in moderately else moderately[key]
                highly[key] = 0 if key not in highly else highly[key]
                if timeseries[t][key] > HIGHLY_CONCENTRATED:
                    highly[key] += 1
                elif timeseries[t][key] > MODERATELY_CONCENTRATED:
                    moderately[key] += 1
    
    for key in total_count:
        table_manager.add_row('four_firm',[key, "% Highly", 100.0 * float(highly[key])/ float(total_count[key])])
        table_manager.add_row('four_firm',[key, "% Moderately", 100.0 * float(moderately[key])/ float(total_count[key])])
      

def get_rsi_stat_table(table_manager, timeseries):
    """Extracts a number of metrics related to RSI"""

    table_manager.set_field_names('rsi', ["Metric","Label", "Value"])

    THRESHOLD = 1
    total_count = {}
    under_threshold = {}
    
    for t in timeseries:
        for key in timeseries[t]:
            if 'minimum_rsi' in key:
                total_count[key] = 1 if key not in total_count else total_count[key] + 1
                under_threshold[key] = 0 if key not in under_threshold else under_threshold[key]
                if timeseries[t][key] < THRESHOLD:
                    under_threshold[key] += 1
                
    
    for key in total_count:
        table_manager.add_row('rsi',[key, "% Under", 100.0 * float(under_threshold[key])/ float(total_count[key])])


def get_nersi_stat_table(table_manager, timeseries):
    """Extracts a number of metrics related to NERSI"""

    table_manager.set_field_names('nersi',["Metric","Label", "Value"] )

    THRESHOLD = 1
    total_count = {}
    under_threshold = {}
    
    for t in timeseries:
        for key in timeseries[t]:
            if 'minimum_nersi' in key:
                total_count[key] = 1 if key not in total_count else total_count[key] + 1
                under_threshold[key] = 0 if key not in under_threshold else under_threshold[key]
                if timeseries[t][key] < THRESHOLD:
                    under_threshold[key] += 1
                
    
    for key in total_count:
        table_manager.add_row('nersi',[key, "% Under", 100.0 * float(under_threshold[key])/ float(total_count[key])])


def get_psi_stat_table(table_manager, timeseries):
    """Extracts a number of metrics related to PSI"""

    table_manager.set_field_names('psi', ["Metric","Label", "Value"])
    total_count = {}
    some_over = {}
    
    for t in timeseries:
        for key in timeseries[t]:
            if 'sum_psi' in key:
                total_count[key] = 1 if key not in total_count else total_count[key] + 1
                some_over[key] = 0 if key not in some_over else some_over[key]
                if timeseries[t][key] > 0:
                    some_over[key] += 1
                
    
    for key in total_count:
        table_manager.add_row('psi', [key, "% w/ PSI", 100.0 * float(some_over[key])/ float(total_count[key])])



def table_data(timeseries):
    table_manager = TableManager()
    get_hhi_stat_table(table_manager, timeseries)
    get_entropy_stat_table(table_manager, timeseries)
    get_four_firm_stat_table(table_manager, timeseries)
    get_psi_stat_table(table_manager, timeseries)
    get_rsi_stat_table(table_manager, timeseries)
    get_nersi_stat_table(table_manager, timeseries)

    table_manager.print_tables()
    table_manager.export_tables_to_csv()