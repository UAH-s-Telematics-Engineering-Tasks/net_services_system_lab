##################################################################################################
#                                       MongoDB Structure                                        #
# MongoDB manages databases composed of collections. These collections in turn                   #
# contain documents which are internally represented as BSON (similar to JSON) objects.          #
# Connecting to MongoDB's daemon is done by running 'mongo'. We have created our own             #
# database running 'use asterisk_data' and then by running the following command we inserted     #
# our first document: db.call_data.insertOne({caller: "foo", called: "fuu", chargeable: true})   #
# the collection call_data is automagically created for us. Note MongoDB is quite lazy when      #
# creating entries so collections and DBs themselves won't show up until we insert a document.   #
# We can then query a collection with db.call_data.find({}) to get every record or we could      #
# issue db.call_data.find({"caller": "pablo"}) to get those documents whose "caller" was "pablo" #
# API calls are mostly the same so we can get on with this info!                                 #
##################################################################################################

import pymongo

def main():
    charging_data = {}
    price_per_call = 0.15

    mongo_client = pymongo.MongoClient('localhost', 27017)
    call_data = mongo_client.asterisk_data.call_data

    for call in call_data.find():
        if call['chargeable']:
            if call['caller'] not in charging_data:
                charging_data[call['caller']] = 0
            charging_data[call['caller']] += 1

    for caller, n_calls in charging_data.items():
        print("{} made {} chargeable call(s) and will be charged {} euros".format(caller.capitalize(), n_calls, n_calls * price_per_call))

    return

if __name__ == '__main__':
    main()