ffprobe -v error -select_streams v:0 -show_entries frame=pts_time,pkt_duration_time,key_frame -of csv=print_section=1 %* >x.log 2>&1 