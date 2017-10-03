"""
Application description
"""
import sys
import os
import logging
import omodeler

METADATA_URL = "https://graph.microsoft.com/v1.0/$metadata"
INPUT_LOCATION = "./input/"
TEMP_LOCATION = "./tmp/"
OUTPUT_LOCATION = "./output/"
LOG_FILENAME = "app.log"
CLASS_PREFIX = "Graph"
CONSOLE_LOG_LEVEL = logging.DEBUG


def main():

    try:
        os.remove(TEMP_LOCATION + LOG_FILENAME)
    except FileNotFoundError:
        pass

    logging.basicConfig(format="%(levelname)s %(message)s", level=CONSOLE_LOG_LEVEL)
    file_log = logging.FileHandler(filename=TEMP_LOCATION + LOG_FILENAME)
    file_log.setLevel(logging.INFO)
    file_log.setFormatter(logging.Formatter("%(asctime)-15s %(levelname)s %(message)s"))
    logging.getLogger('').addHandler(file_log)
    logging.debug("Start")

    graph_model = omodeler.ClassFactory(METADATA_URL, CLASS_PREFIX, INPUT_LOCATION, TEMP_LOCATION)
    graph_model.save(OUTPUT_LOCATION)

    logging.debug("Finished")
    return 0

if __name__ == '__main__':
    sys.exit(main())
