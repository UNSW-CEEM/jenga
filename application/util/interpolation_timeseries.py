import pendulum
import csv
class InterpolationTimeseries():
    def __init__(self):
        self.data = []
        
    
    def add(self, date_time, data_dict):
        # Get the required index for the insert
        index = 0
        
        for item in self.data:
            if item['date_time'] > date_time:
                break
            index += 1
        
        data_dict['date_time'] = date_time
        self.data.insert(index, data_dict)
        # print("---")
        # [print(i) for i in self.data]

    def get(self, date_time, dict_key):
        index = -1
        for item in self.data:
            if item['date_time'] > date_time:
                break
            index += 1
        
        if index >= len(self.data)-1:
            return self.data[len(self.data)-1][dict_key]
        elif index == -1:
            return self.data[0][dict_key]
        else:
            return self._interpolate(
                self.data[index]['date_time'],
                self.data[index][dict_key],
                self.data[index+1]['date_time'],
                self.data[index+1][dict_key],
                date_time
            )

    def _interpolate(self, dt_1, v1, dt_2, v2, dt_3):
        # print("Interpolating", dt_3)
        # print(dt_1, v1)
        # print(dt_2, v2)
        fraction_along = (dt_3.timestamp() - dt_1.timestamp())/(dt_2.timestamp() - dt_1.timestamp())
        # print(fraction_along)
        return float(fraction_along) * float(v2) + float(1-fraction_along) * float(v1)



class NormalisedRenewablesNinjaTimeseries(InterpolationTimeseries):
    def __init__(self,renewables_ninja_source_path=None):
        super(NormalisedRenewablesNinjaTimeseries, self).__init__()
        with open(renewables_ninja_source_path) as f:
            next(f)
            next(f)
            reader = csv.DictReader(f)
            for line in reader:
                self.add(pendulum.parse(line['UTC']), line)



if __name__ == "__main__":
    it = InterpolationTimeseries()
    start = pendulum.now()
    
    for i in range(10):
        it.add(start.add(hours=i), {'kW':i})

    print(it.get(start.add(minutes=15), 'kW'))
    

        

