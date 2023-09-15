#!/usr/bin/env python -u

import os
import shutil
import time
import ffmpeg
from parse_ffprobe_log import LogParse

# ffmpeg -hide_banner -ss '3299.70956' -i 'in.mp4' -t '1004.09714'
# -avoid_negative_ts make_zero -map '0:0' '-c:0' copy -map '0:1' '-c:1' copy
# -map_metadata 0 -movflags '+faststart'
# -default_mode infer_no_subs -ignore_unknown -strict experimental -f avi
# -y 'out.avi'


def get_ffprobe_properties(file):
    ffmpeg_properties = {}
    try:
        ffmpeg_probe = ffmpeg.probe(file)

        if 'streams' in ffmpeg_probe:
            for stream in ffmpeg_probe['streams']:
                if 'coded_height' in stream:
                    ffmpeg_properties['height'] = stream['coded_height']
                    if stream['codec_name'] == 'mpeg4':
                        ffmpeg_properties['codec'] = 'xvid'
                    else:
                        ffmpeg_properties['codec'] = stream['codec_name']
                    file_height = stream['coded_height']
                    # file_height in [2160, 1080, 720, 540, 544, 480, 360, 320]:
                    if True:
                        ffmpeg_properties['resolution'] = str(
                            file_height) + 'p'
                if 'coded_width' in stream:
                    ffmpeg_properties['width'] = stream['coded_width']
    except (ffmpeg.Error) as err:
        logger.error('ffprobe error: %s', err)
        return False

    return ffmpeg_properties


def extract_dmg_frames(framedmg, file):
    start = framedmg.last_keyframe
    duration = framedmg.recovery_keyframe - start + 0.5
    # print(start)
    # print(framedmg.recovery_frame)
    # print(duration)
    xxx = ffmpeg.input(file, ss=start, t=duration,)
    xxx = ffmpeg.output(xxx, 'err_start%03d.png')
    ffmpeg.run(xxx, overwrite_output=False)

    # start = framedmg.recovery_frame
    # xxx = ffmpeg.input(file, ss=start, t=duration)
    # xxx = ffmpeg.output(xxx, 'err_end%03d.png')
    # ffmpeg.run(xxx, overwrite_output=False)


def extract_donor_frames(framedmg, file, ffmpeg_props):
    width = ffmpeg_props['width']
    height = ffmpeg_props['height']
    start = framedmg.last_keyframe
    duration = framedmg.recovery_keyframe - start +0.5
    xxx = ffmpeg.input(file, ss=start, t=duration)
    xxx = ffmpeg.output(xxx, 'donor%03d.png', s='{}x{}'.format(width, height))
    ffmpeg.run(xxx, overwrite_output=False)


def extract_dmg(logparse, file):
    dmg_num = 0
    curr_dir = os.getcwd()
    for framedmg in logparse.dmg_list:
        dmg_str = str(dmg_num)
        while len(dmg_str) < 5:
            dmg_str = '0'+dmg_str
        os.chdir(dmg_str)
        extract_dmg_frames(framedmg, file)
        os.chdir(curr_dir)
        dmg_num += 1


def extract_donor(logparse, file, ffmpeg_props):
    dmg_num = 0
    curr_dir = os.getcwd()
    for framedmg in logparse.dmg_list:
        dmg_str = str(dmg_num)
        while len(dmg_str) < 5:
            dmg_str = '0'+dmg_str
        try:
            os.mkdir(dmg_str)
        except FileExistsError:
            pass

        os.chdir(dmg_str)
        extract_donor_frames(framedmg, file, ffmpeg_props)
        os.chdir(curr_dir)
        dmg_num += 1


def main():
    logparse = LogParse()
    logparse.load_dmg_list(args.parse_file)
    base_dir = os.getcwd()
    tmp_dir = os.path.join(base_dir, args.parse_file+'_TMP')
    try:
        os.mkdir(tmp_dir)
    except FileExistsError:
        pass

    os.chdir(tmp_dir)
    corrupted_file = os.path.join(base_dir, args.corrupted_file)
    donor_file = os.path.join(base_dir, args.donor_file)
    ffmpeg_props = get_ffprobe_properties(corrupted_file)
    print(ffmpeg_props)
    extract_donor(logparse, donor_file, ffmpeg_props)
    extract_dmg(logparse, corrupted_file)


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
        description='Split corrupted file using parsed log')
    parser.add_argument('parse_file', help='parsed log file')
    parser.add_argument('corrupted_file', help='corrupted media file')
    parser.add_argument('donor_file', help='file to get frames from')

    args = parser.parse_args()

    time_start = time.time()
    main()
    time_end = time.time()
    total_time = time_end - time_start
    print("\nExecution time: " + str(total_time))
