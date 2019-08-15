from opennempy import web_api
df_5, df_30 = web_api.load_data(d1 = datetime.datetime(2018,3,4), d2 = datetime.datetime(2018,4,19), region='sa1')
print(df_30)