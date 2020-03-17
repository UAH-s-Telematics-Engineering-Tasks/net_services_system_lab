#!/usr/bin/python3

import pymongo
import asterisk.agi as agi

chargeable_endpoints = ['pablo', 'alice']

def main():
    agi_inst = agi.AGI()

    agi_inst.verbose("Connecting to MongoDB")
    mongo_client = pymongo.MongoClient('localhost', 27017)

    agi_inst.verbose("Retrieving Call Data")
    calls = mongo_client.asterisk_data.call_data

    agi_inst.verbose("Got the collection")

    gathered_data = {
            "caller": agi_inst.env['agi_callerid'],
            "called": agi_inst.env['agi_arg_1'],
            "chargeable": agi_inst.env['agi_arg_1'] in chargeable_endpoints
        }

    agi_inst.verbose("Gathered data: " + str(gathered_data))

    calls.insert_one(gathered_data)

    agi_inst.verbose("Inserted data. Time to go!")

if __name__ == '__main__':
    main()