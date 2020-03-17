#!/usr/bin/python3

import asterisk.agi as agi

def main():
    agi_inst = agi.AGI()
    agi_inst.verbose("python agi started")
    callerId = agi_inst.env['agi_callerid']
    agi_inst.verbose("call from %s" % callerId)
    while True:
        agi_inst.stream_file('vm-extension')
        result = agi_inst.wait_for_digit(-1)
        agi_inst.verbose("got digit %s" % result)
        if result.isdigit():
            agi_inst.say_number(result)
        else:
            agi_inst.verbose("bye!")
            agi_inst.hangup()
            agi_inst.exit()


if __name__ == '__main__':
    main()
