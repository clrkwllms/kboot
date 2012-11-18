#!/usr/bin/python -tt

import os
import sys
import subprocess

if os.getuid() != 0:
    raise RuntimeError, "must be root!"

kernel = []
for l in open('/etc/grub.conf'):
    if l.startswith('title'):
        kernel.append("%s" % l[6:-1])

if len(sys.argv) <= 1:
    for i in range(0,len(kernel)):
        print "%d %s" % (i, kernel[i])
    index = int(raw_input("Select kernel to boot: "))
else:
    index = int(sys.argv[1])

if index < 0 or index >= len(kernel):
    raise ValueError, "invalid grub index %d (valid range: 0 - %d)" % (index, len(kernel)-1)

p = subprocess.Popen(["/sbin/grub", "--batch"], stdin=subprocess.PIPE)
p.stdin.write("savedefault --default=%d --once\n" % index)
p.stdin.close()
ret = p.wait()
if ret:
    raise RuntimeError, "call to grub failed! (%d)" % ret

subprocess.call("reboot", shell=True)
