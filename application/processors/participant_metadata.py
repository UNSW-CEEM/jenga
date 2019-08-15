import csv
import os
from application.model.participants import Participant
from string import digits
remove_digits = str.maketrans('', '', digits)
import re

if __name__ == "__main__":

    with open(os.path.join('data', 'participant_metadata.csv')) as f:
        reader = csv.DictReader(f)
        for line in reader:
            print(line)
            p = Participant(
                label = line['\ufeffParticipant'],
                parent_firm = line['Parent Firm'],
                station_name = line['Station Name'],
                region = line['Region'],
                state = line['Region'].translate(remove_digits),
                dispatch_type = line['Dispatch Type'],
                category = line['Category'],
                classification = line['Classification'],
                fuel_source_primary = line['Fuel Source - Primary'],
                fuel_source_descriptor = line['Fuel Source - Descriptor'],
                technology_type_primary = line['Technology Type - Primary'],
                technology_type_descriptor = line['Technology Type - Descriptor'],
                physical_unit_no = line['Physical Unit No.'],
                unit_size_MW = float(line['Unit Size (MW)']) if re.match("^\d+?\.\d+?$", line['Unit Size (MW)']) else None,
                aggregation = line['Aggregation'],
                DUID = line['DUID'],
                reg_cap_MW = float(line['Reg Cap (MW)']) if re.match("^\d+?\.\d+?$", line['Reg Cap (MW)']) else None,
                max_cap_MW = float(line['Max Cap (MW)']) if re.match("^\d+?\.\d+?$", line['Max Cap (MW)']) else None,
                max_ROC_per_min = float(line['Max ROC/Min']) if re.match("^\d+?\.\d+?$", line['Max ROC/Min']) else None,
            )
            p.save()