from mongoengine import *

class Processed_File(Document):
    file_name = StringField()

def set_processed(file_name):
    f = Processed_File(file_name)
    f.save()


def check_processed(file_name):
    if Processed_File.objects(file_name=file_name):
        return True
    return False

if __name__=="__main__":
    print(check_processed('test'))
    set_processed('test')
    print(check_processed('test'))