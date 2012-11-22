#!/usr/bin/python -tt

import os
import sys
import os.path
import subprocess

def get_kernels(version):
    kernels =  []
    if version == 1:
        for l in open('/etc/grub.conf'):
            if l.startswith('title'):
                kernels.append(l[6:-1])
    else:
        for l in open('/etc/grub2.cfg'):
            if l.startswith('menuentry'):
                kernels.append(l[11:l.find('--class') - 2])
    return kernels

def do_reboot(version, index):
    if version == 1:
        p = subprocess.Popen(["/sbin/grub", "--batch"], stdin=subprocess.PIPE)
        p.stdin.write("savedefault --default=%d --once\n" % index)
        p.stdin.close()
        ret = p.wait()
        if ret:
            raise RuntimeError, "call to grub failed! (%d)" % ret
    else:
        #print "/sbin/grub2-reboot %d" % index
        subprocess.call("/sbin/grub2-reboot %d" % index, shell=True)
    subprocess.call("reboot", shell=True)

#####################################################################

if os.getuid() != 0:
    raise RuntimeError, "must be root!"

if os.path.exists('/sbin/grub2-reboot'):
    grub_version = 2
else:
    grub_version = 1

kernel = get_kernels(grub_version)

if len(sys.argv) <= 1:
    for i in range(0,len(kernel)):
        print "%d %s" % (i, kernel[i])
    index = int(raw_input("Select kernel to boot: "))
else:
    index = int(sys.argv[1])

if index < 0 or index >= len(kernel):
    raise ValueError, "invalid grub index %d (valid range: 0 - %d)" % (index, len(kernel)-1)

do_reboot(grub_version, index)
