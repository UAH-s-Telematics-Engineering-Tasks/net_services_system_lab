from google.cloud import speech_v1p1beta1
from google.cloud.speech_v1p1beta1 import enums
import sys


def sample_recognize():
    client = speech_v1p1beta1.SpeechClient()
    config = {
        "language_code": "en-US",
        "sample_rate_hertz": 8000,
    }
    audio = {"content": open(sys.argv[1], 'rb').read()}

    response = client.recognize(config, audio)
    for result in response.results:
        # First alternative is the most probable result
        alternative = result.alternatives[0]
        print(alternative)
        print(type(alternative.transcript))
        print(u"Transcript: {}".format(alternative.transcript))

if __name__=="__main__":
    sample_recognize()
