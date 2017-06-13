"""
Application description
"""
import sys
import os
import logging
import openschema.factory

LOG_FILENAME = "run.log"

METADATA_URL = "https://graph.microsoft.com/v1.0/$metadata"
INPUT_LOCATION = "./input/"
TEMP_LOCATION = "./tmp/"
OUTPUT_LOCATION = "./output/"


def main():

    try:
        os.remove(TEMP_LOCATION + LOG_FILENAME)
    except FileNotFoundError:
        pass
    log_format = '%(asctime)-15s %(levelname)s %(message)s'
    logging.basicConfig(filename=TEMP_LOCATION + LOG_FILENAME, format=log_format, level=logging.DEBUG)
    logging.info('Started')

    graph_model = openschema.factory.ClassFactory(METADATA_URL, TEMP_LOCATION, OUTPUT_LOCATION)

    logging.info('Finished')

if __name__ == '__main__':
    sys.exit(main())
