from nemosis import data_fetch_methods
import os
import pendulum
import application.processors.period_offers as process_period_offers
import application.processors.day_offers as process_day_offers
import application.processors.generate_bid_objects as bid_objects
import application.model.processed_files as processed_files

def check_file_exists(path, fname):
        files = os.listdir(path)
        if not fname in files:
            return False
        else:
            return True



def download_period_offers(year, month):
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


def run_period_offers(year, month):
    expected_fname = "PUBLIC_DVD_BIDPEROFFER_D_"+str(year)+str(month).zfill(2)+"010000.CSV"
    # If the file isn't in the folder, use nemosis to download it. 
    if not check_file_exists(os.path.join(raw_data_cache, 'BIDPEROFFER_D'), expected_fname):
        download_period_offers(year, month)
    # Load the file into the database
    if not processed_files.check_processed(expected_fname):
        print("Processing Period Offer", year, month)
        process_period_offers.process(os.path.join(raw_data_cache,'BIDPEROFFER_D',expected_fname))
        processed_files.set_processed(expected_fname)


def download_day_offers(year, month):
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

def run_day_offers(year, month):
    expected_fname = "PUBLIC_DVD_BIDDAYOFFER_D_"+str(year)+str(month).zfill(2)+"010000.CSV"
    # If the file isn't in the folder, use nemosis to download it. 
    if not check_file_exists(os.path.join(raw_data_cache, 'BIDDAYOFFER_D'), expected_fname):
        download_day_offers(year, month)
    # Load the file into the database
    if not processed_files.check_processed(expected_fname):
        print("Processing Day Offer", year, month)
        process_day_offers.process(os.path.join(raw_data_cache,'BIDDAYOFFER_D',expected_fname))
        processed_files.set_processed(expected_fname)





if __name__=="__main__":

    raw_data_cache = 'data'

    years = [2015]
    months = [1,2,3,4,5,6,7,8,9,10,11,12]

    # Download the relevant files. 
    for year in years:
        for month in months:
            download_period_offers(year, month)
            download_day_offers(year, month)

    # Process the downloaded files
    for year in years:
        for month in months:
            run_period_offers(year, month)
            run_day_offers(year, month)
    
    # Generate the bid objects.
    for year in years:
        for month in months:
            start_date = pendulum.datetime(year, month, 1,0,0,0)
            end_date = pendulum.instance(start_date).end_of('month')
            bid_objects.generate(start_date, end_date)
        
       




# period_offers = 



