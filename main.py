"""
Application description
"""
import sys
from model import GraphModel
import logging


def main():
    log_file_name = 'run.log'
    log_format = '%(asctime)-15s %(levelname)s %(message)s'
    logging.basicConfig(filename=log_file_name, format=log_format, level=logging.DEBUG)
    logging.info('Started')

    model_file_name = 'model.json'
    metadata_url = 'https://graph.microsoft.com/v1.0/$metadata'

    graph_model = GraphModel(model_file_name, metadata_url)

    logging.info('Finished')

if __name__ == '__main__':
    sys.exit(main())
