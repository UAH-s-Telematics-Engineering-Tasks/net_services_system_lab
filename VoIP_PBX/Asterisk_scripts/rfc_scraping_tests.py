#!/usr/bin/python3

# NOTE: Remember to add Google's API key with 'export GOOGLE_APPLICATION_CREDENTIALS="/home/vagrant/g_api_key.json"'

import urllib.request
from google.cloud import speech_v1p1beta1
from google.cloud.speech_v1p1beta1 import enums
import sys, os
import asterisk.agi as agi

agi_inst = agi.AGI()

def recognize_voice(voice_file):
    agi_inst.verbose(voice_file)
    w_2_d = {
        'zero': '0',
        'one': '1',
        'two': '2',
        'three': '3',
        'four': '4',
        'five': '5',
        'six': '6',
        'seven': '7',
        'eight': '8',
        'nine': '9'
    }

    client = speech_v1p1beta1.SpeechClient()
    config = {
        "language_code": "en-US",
        "sample_rate_hertz": 8000,
    }
    audio = {"content": open(voice_file, 'rb').read()}

    response = client.recognize(config, audio)
    # for result in response.results:
    #     alternative = result.alternatives[0]
    #     print(u"Transcript: {}".format(alternative.transcript))

    trans_text = response.results[0].alternatives[0].transcript
    num = ""
    if ' ' in trans_text:
        for dig in trans_text.split(' '):
            num += w_2_d[dig]
    else:
        num = trans_text

    agi_inst.verbose("Translated speech: {}".format(num))

    return num

    # PASSING RFCs
    # SMI -> 1155
    # UDP -> 768
    # TCP -> 793
    # IP -> 791
    # HTTP -> 2616

def scrap_rfc(rfc_id):
    rfc = urllib.request.urlopen('https://tools.ietf.org/rfc/rfc{}.txt'.format(rfc_id))

    agi_inst.verbose("Downloaded RFC {}".format(rfc_id))

    began_doc = False
    reading_title = False
    whiteline = 0
    title = ""

    email = 'From: "Foo" <foo@home.net>\nTo: "You" <pcolladosoto@gmail.com>\nSubject: RCF {} Title\nMIME-Version: 1.0\nContent-Type: text/plain\n\n{}\n.\n'

    for line in rfc:
        if line.decode().strip() == '' or line.decode().isspace() or not line.decode().strip(' \n').isprintable() or '-----------' in line.decode():
            whiteline += 1
        else:
            if not began_doc:
                began_doc = True
                whiteline = 0
            elif whiteline <= 1 and not reading_title:
                whiteline = 0
            elif whiteline >= 2 and not reading_title and began_doc:
                reading_title = True
                title += line.decode()
                whiteline = 0
            elif reading_title and 'Table of Contents' not in line.decode() and 'Memo' not in line.decode():
                title += line.decode()

        if reading_title and (whiteline > 1 or 'Table of Contents' in line.decode() or 'Memo' in line.decode()):
            break

    agi_inst.verbose("Got title: {}".format(title.strip()))

    # email_file = open("/tmp/email.txt", "w")
    # email_file.write(email.format(rfc_id, title.strip()))
    # email_file.close()

    agi_inst.verbose("Sending mail!")

    # os.system("cat /tmp/email.txt | sendmail -i -t -v")

    os.system("echo '{}' | sendmail -t".format(email.format(rfc_id, title.strip())))

    agi_inst.verbose("Creating title audio file!")

    os.system("echo '{}' | /usr/bin/text2wave -scale 1.5 -F 8000 -o /tmp/title.wav".format(title.strip()))

def main():
    agi_inst.verbose("Script started!")
    # agi_inst.verbose(str(agi_inst.env))
    foo = recognize_voice(agi_inst.env['agi_arg_1'])
    scrap_rfc(foo)
    return 0

if __name__=='__main__':
    main()