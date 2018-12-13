from application.model.price import Price

print('Deleting BASIC_VCG')
for price in Price.objects(price_type='BASIC_VCG'):
    print(price)
    price.delete()
print('Finished Deleting.')