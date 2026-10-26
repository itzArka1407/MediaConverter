# Create a source MP3
ffmpeg -f lavfi -i "sine=frequency=440:duration=2" -c:a libmp3lame -b:a 192k ./test_shell_cmds/aud_in.mp3
