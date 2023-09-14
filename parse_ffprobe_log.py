#!/usr/bin/env python -u
import re


# ffprobe -v error -select_streams v:0
# -show_entries frame=pts_time,pkt_duration_time,key_frame
# -of csv=print_section=1 x.mp4 2>1 >x.log

import time


class LogParse:
    def __init__(self) -> None:
        self.lastframenum = 0
        self.frames_read = 0
        self.lines_parsed = 0
        self.last_timestamp = 0
        self.duration_total = 0
        self.error_tolerance = 0.1
        self.errorcount = 0
        self.last_keyframe = 0

        # frame,16.200000,0.040000,side_data,timecode,
        self.r_error = r'missing picture in access unit'
        self.r_frame = r'^frame,([01]),(\d+\.\d+),(\d+\.\d+)'

    def parse(self, line):
        self.lines_parsed += 1

        matching = re.search(self.r_error, line)
        if matching:
            self.errorcount +=1
            #logger.info('missing frame')
            return True

        matching = re.search(self.r_frame, line)
        if matching:
            if self.errorcount:
                logger.info('errorcount %s', self.errorcount)
                self.errorcount = 0

            is_keyframe = int(matching.group(1))
            timestamp = float(matching.group(2))
            duration = float(matching.group(3))
            if is_keyframe:
                self.last_keyframe = timestamp
            logger.debug('%s %s', timestamp, duration)

            avg_duration = (self.duration_total + duration) / \
                (self.frames_read + 1)

            if abs((self.last_timestamp - timestamp)) > avg_duration*(1+self.error_tolerance):
                logger.info('missing frame found at %s', self.last_timestamp)
                missing_frames = (timestamp - self.last_timestamp -avg_duration) / avg_duration
                logger.info('estimated %s frames missing', missing_frames)
                logger.info('Last keyframe %s %s', self.lastframenum, self.last_keyframe)
                self.lastframenum += int(round(missing_frames,0))


        # print(avg_duration, timestamp, self.last_timestamp)
            self.frames_read += 1
            self.duration_total += duration
            self.last_timestamp = timestamp
            self.lastframenum +=1
            return True

        logger.debug('regexp match fail on %s', line)
        return False

def main():
    logparse = LogParse()
    with open(args.log_file, 'r') as log:
        for line in log:
            logparse.parse(line)


if __name__ == "__main__":
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    #fh = logging.FileHandler(__name__ + '.txt')
    #fh.setLevel(logging.DEBUG)
    #fh.setFormatter(formatter)
    sh = logging.StreamHandler()
    sh.setLevel(logging.DEBUG)
    sh.setFormatter(formatter)

    # logger.addHandler(fh)
    logger.addHandler(sh)

    from argparse import ArgumentParser
    parser = ArgumentParser(
        description='Parse output of ffprobe')
    parser.add_argument('log_file', help='ffprobe log file')

    args = parser.parse_args()


    time_start = time.time()
    main()
    time_end = time.time()
    total_time = time_end - time_start
    print("\nExecution time: " + str(total_time))
