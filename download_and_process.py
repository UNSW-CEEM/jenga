from nemosis import data_fetch_methods
import os
import pendulum
import process_period_offers
import process_day_offers
import application.model.processed_files as processed_files

def check_file_exists(path, fname):
        files = os.listdir(path)
        if not fname in files:
            return False
        else:
            return True



def run_period_offers(year, month):
    expected_fname = "PUBLIC_DVD_BIDPEROFFER_D_"+str(year)+str(month).zfill(2)+"010000.CSV"
    # If the file isn't in the folder, use nemosis to download it. 
    if not check_file_exists(os.path.join(raw_data_cache, 'BIDPEROFFER_D'), expected_fname):
        print("File not found - fetching via NEMOSIS", expected_fname)
        start_time = pendulum.datetime(year,month,1,0,0).format('YYYY/MM/DD HH:mm:ss')
        end_time = pendulum.datetime(year,month,1,0,5).format('YYYY/MM/DD HH:mm:ss')
        print(start_time, end_time)
        # end_time = '2018/01/01 00:05:00'
        table = 'BIDPEROFFER_D'
        data_fetch_methods.dynamic_data_compiler(start_time, end_time, table, os.path.join(raw_data_cache, 'BIDPEROFFER_D'))
    # Load the file into the database
    if not processed_files.check_processed(expected_fname):
        process_period_offers.process(os.path.join(raw_data_cache,'BIDPEROFFER_D',expected_fname))
        processed_files.set_processed(expected_fname)


def run_day_offers(year, month):
    expected_fname = "PUBLIC_DVD_BIDDAYOFFER_D_"+str(year)+str(month).zfill(2)+"010000.CSV"
    # If the file isn't in the folder, use nemosis to download it. 
    if not check_file_exists(os.path.join(raw_data_cache, 'BIDDAYOFFER_D'), expected_fname):
        print("File not found - fetching via NEMOSIS", expected_fname)
        start_time = pendulum.datetime(year,month,2,0,0).format('YYYY/MM/DD HH:mm:ss')
        end_time = pendulum.datetime(year,month,2,0,5).format('YYYY/MM/DD HH:mm:ss')
        print(start_time, end_time)
        # end_time = '2018/01/01 00:05:00'
        table = 'BIDDAYOFFER_D'
        data_fetch_methods.dynamic_data_compiler(start_time, end_time, table, os.path.join(raw_data_cache, 'BIDDAYOFFER_D'))
    # Load the file into the database
    if not processed_files.check_processed(expected_fname):
        process_day_offers.process(os.path.join(raw_data_cache,'BIDDAYOFFER_D',expected_fname))
        processed_files.set_processed(expected_fname)





if __name__=="__main__":

    raw_data_cache = 'data'

    years = [2018]
    months = [1,2,3,4,5,6,7,8,9,10,11,12]

    for year in years:
        for month in months:
            run_period_offers(year, month)
            run_day_offers(year, month)
        
       




# period_offers = 



