# Simple html decoder from stdin to stdout
import html
import fileinput

for line in fileinput.input():
    print(html.unescape(line.strip()))
