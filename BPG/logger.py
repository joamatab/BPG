import logging
from datetime import datetime


def setup_logger(logfile: str = 'bpg.log',
                 verbose: bool = False,
                 ) -> None:
    """

    Parameters
    ----------
    logfile
    verbose

    Returns
    -------

    """
    """ Configures the root logger so that all other loggers in BPG inherit from its properties """

    # Set up the initial basic config for the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.handlers = []

    # Add a console handler
    out_handler = logging.StreamHandler()
    # If the verbose option is set to False, only display warnings and errors
    if verbose is False:
        out_handler.setLevel(logging.INFO)
    else:
        out_handler.setLevel(logging.INFO)

    # Add an output file to the root logger, overwrite the log file if it already exists
    file_handler = logging.FileHandler(logfile, 'w')
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(filename)s:%(lineno)d] %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    file_handler_info = logging.FileHandler(logfile + '_INFO', 'w')
    file_handler_info.setLevel(logging.INFO)
    file_handler_info.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(file_handler_info)
    logger.addHandler(out_handler)

    # Print out the current date and time
    logger.info('##########################')
    logger.info('Starting BPG Build')
    time = datetime.now()
    logger.info(str(time))
    logger.info('##########################')

    # Set up a dataprep logger for dumping dataprep debug data
    dataprep_logger = logging.getLogger(name='dataprep')
    dataprep_logger.setLevel(logging.DEBUG)
    dataprep_logger.handlers = []

    # Add a file stream for the dataprep logger
    dataprep_file_handler = logging.FileHandler()
