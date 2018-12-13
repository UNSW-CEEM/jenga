from application.model.price import Price

print('Deleting LMP')
counter = 0
for price in Price.objects(price_type='LMP'):
    price.delete()
    print(counter)
    counter += 1
print('Finished Deleting.')