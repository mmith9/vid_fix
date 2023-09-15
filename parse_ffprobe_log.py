#!/usr/bin/env python -u
import re


# ffprobe -v error -select_streams v:0
# -show_entries frame=pts_time,pkt_duration_time,key_frame
# -of csv=print_section=1 x.mp4 2>1 >x.log

import time


class FrameDamage:
    def __init__(self) -> None:
        self.last_keyframe = None
        self.last_good = None
        self.recovery_frame = None
        self.number_of_corruptions = None
        self.recovery_keyframe = None

    def to_str(self):
        line = f'\
{self.last_keyframe},{self.last_good},{self.recovery_frame},{self.number_of_corruptions},\
{self.recovery_keyframe}\
\n'
        return line

    def from_str(self, line):
        regex = r'([0-9\.]+),([0-9\.]+),([0-9\.]+),([0-9\.]+),([0-9\.]+)'
        matching = re.search(regex, line)
        if matching:
            self.last_good = float(matching.group(1))
            self.last_keyframe = float(matching.group(2))
            self.recovery_frame = float(matching.group(3))
            self.number_of_corruptions = int(matching.group(4))
            self.recovery_keyframe = float(matching.group(5))
            return True
        return False
        

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
        self.dmg_list = []
        self.corruptions_total = 0

        # frame,16.200000,0.040000,side_data,timecode,
        self.r_error = r'missing picture in access unit'
        self.r_frame = r'^frame,([01]),(\d+\.\d+),(\d+\.\d+)'

    def parse(self, line):
        self.lines_parsed += 1

        matching = re.search(self.r_error, line)
        # if matching:
        #     self.errorcount +=1
        #     #logger.info('missing frame')
        #     return True

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
                if self.dmg_list:
                    if not self.dmg_list[-1].recovery_keyframe:
                        self.dmg_list[-1].recovery_keyframe = timestamp
                        
            logger.debug('%s %s', timestamp, duration)

            avg_duration = (self.duration_total + duration) / \
                (self.frames_read + 1)

            if abs((self.last_timestamp - timestamp)) > avg_duration*(1+self.error_tolerance):

                logger.info('missing frame found at %s', self.last_timestamp)
                missing_frames = (
                    timestamp - self.last_timestamp - avg_duration) / avg_duration
                missing_frames = int(round(missing_frames, 0))
                logger.info('estimated %s frames missing', missing_frames)
                logger.info('Last keyframe %s %s',
                            self.lastframenum, self.last_keyframe)
                self.lastframenum += int(round(missing_frames, 0))
                self.corruptions_total += missing_frames

                framedmg = FrameDamage()
                framedmg.last_good = self.last_timestamp
                framedmg.recovery_frame = timestamp
                framedmg.number_of_corruptions = missing_frames
                framedmg.last_keyframe = self.last_keyframe
                self.dmg_list.append(framedmg)

        # print(avg_duration, timestamp, self.last_timestamp)
            self.frames_read += 1
            self.duration_total += duration
            self.last_timestamp = timestamp
            self.lastframenum += 1
            return True

        logger.debug('regexp match fail on %s', line)
        return False

    def save_dmg_list(self, filename):
        with open(filename, 'w', encoding='utf-8') as fp:
            for framedmg in self.dmg_list:
                fp.write(framedmg.to_str())

    def load_dmg_list(self, filename):
        self.dmg_list = []
        with open(filename, 'r', encoding='utf-8') as fp:
            for line in fp:
                framedmg = FrameDamage()
                if framedmg.from_str(line):
                    self.dmg_list.append(framedmg)
                  

def main():
    logparse = LogParse()
    with open(args.log_file, 'r') as log:
        for line in log:
            logparse.parse(line)
    print('corruptions ', len(logparse.dmg_list),
          'corrupted frames', logparse.corruptions_total)
    if args.parse_file:
        logparse.save_dmg_list(args.parse_file)


if __name__ == "__main__":
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    # fh = logging.FileHandler(__name__ + '.txt')
    # fh.setLevel(logging.DEBUG)
    # fh.setFormatter(formatter)
    sh = logging.StreamHandler()
    sh.setLevel(logging.DEBUG)
    sh.setFormatter(formatter)

    # logger.addHandler(fh)
    logger.addHandler(sh)

    from argparse import ArgumentParser
    parser = ArgumentParser(
        description='Parse output of ffprobe')
    parser.add_argument('log_file', help='ffprobe log file')
    parser.add_argument('-o', dest='parse_file', type=str,
                        help='save output to file xx')

    args = parser.parse_args()

    time_start = time.time()
    main()
    time_end = time.time()
    total_time = time_end - time_start
    print("\nExecution time: " + str(total_time))
