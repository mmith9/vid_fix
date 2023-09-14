#!/usr/bin/env python -u



#ffprobe -v error -select_streams v:0 -show_entries frame=pts_time,pkt_duration_time -of csv=print_section=1 x.mp4 2>1 >x.log

import time


def main():
    pass


if __name__ == "__main__":
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh = logging.FileHandler(__name__ + '.txt')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    sh = logging.StreamHandler()
    sh.setLevel(logging.DEBUG)
    sh.setFormatter(formatter)

    # logger.addHandler(fh)
    logger.addHandler(sh)

    from argparse import ArgumentParser
    parser = ArgumentParser(
        description='Parse output of ffprobe')
    parser.add_argument('file1', help='The first file')


    args = parser.parse_args()
    args.buffer_size = args.buffer_size * 1024 * 1024

    time_start = time.time()
    main()
    time_end = time.time()
    total_time = time_end - time_start
    print("\nExecution time: " + str(total_time))
