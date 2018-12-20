from application.model.price import Price

print('Deleting LMP VCG')
counter = 1
for price in Price.objects(price_type='LMP_VCG'):
    counter +=1
    print(price, counter)
    price.delete()
print('Finished Deleting.')