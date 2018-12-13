from application.model.price import Price

print('Deleting BASIC')
for price in Price.objects(price_type='BASIC'):
    price.delete()
print('Finished Deleting.')