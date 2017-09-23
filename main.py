import logging
from multiprocessing import Process, Manager
from optparse import OptionParser

from models import PivotCacheRecords
from utils import spreadsheetml_parser


def _parse_console_input():
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename",
                      help="Path to input file", metavar="FILE")
    parser.add_option("-o", "--output", dest="outputname",
                      help="Path to output file", metavar="FILE")
    parser.add_option("-n", "--nchunks", dest="nchunks", default=5, type="int",
                      help="Path to output file", metavar="FILE")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
                      help="Log in console", metavar="FILE")
    (options, _) = parser.parse_args()

    if options.filename is None:
        parser.error("Filename not given")
    if options.verbose is True:
        logging.basicConfig(level=logging.DEBUG)
    if options.outputname is None:
        file_name = options.filename.split('.')
        options.outputname = file_name[0] + ".csv"

    return options.filename, options.outputname, options.nchunks


def _write_csv(io, string):
    file = None
    try:
        file = open(io, "w")
        file.write("".join(string))
        file.flush()
    except IOError:
        logging.error("Output file couldn't be opened")
    finally:
        file.close()


if __name__ == "__main__":
    file_name, output_file, n_chunks = _parse_console_input()
    batch_string = Manager().list()

    logging.info("Extracting pivotCacheRecords from %s..", file_name)
    xmls = PivotCacheRecords(file_name).read()

    for idy, xml in zip(range(1, len(xmls) + 1), xmls):
        logging.info("Splitting pivotCacheRecords%d.xml into %d chunks", idy, n_chunks)
        chunks = spreadsheetml_parser.split_xml(xml, n_chunks)

        for idx in range(len(chunks)):
            logging.info("Converting chunk %d of pivotCacheRecords%d.csv", idx, idy,)
            valid_xml = spreadsheetml_parser.get_valid_spreadsheetml(chunks, idx)

            logging.debug("Chunk head %s", valid_xml[:200])
            logging.debug("Chunk tail %s", valid_xml[-200:])
            p = Process(target=spreadsheetml_parser.str_xml_to_csv, args=(valid_xml, batch_string,))

            p.start()
            p.join()
            logging.info("Chunk %d of pivotCacheRecords%d.csv successfully converted", idx, idy)

        logging.info("Saving result in %s...", output_file)
        _write_csv(output_file + '-' + str(idy), batch_string)
        logging.info("CSV File %s successfully created", output_file)




