from application.model.price import Price

print('Deleting TOTAL_INDUSTRIAL_COST')
counter = 0
for price in Price.objects(price_type='TOTAL_INDUSTRIAL_COST'):
    print(price, counter)
    price.delete()
    counter += 1
print('Finished Deleting.')