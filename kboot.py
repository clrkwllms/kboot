#!/usr/bin/python -tt

import os
import sys
import os.path
import subprocess

class Kernel(object):
    __slots__ = ('index', 'description', 'path')
    def __init__(self, index, desc, path):
        self.index = index
        self.description = desc
        self.path = path

class Grub1(object):
    def __init__(self):
        self.kernels = []
        index = 0
        for l in open('/etc/grub.conf'):
            l = l.strip()
            if l.startswith('title'):
                k = Kernel(l[6:-1], index)
                continue
            if l.startswith('kernel'):
                p = l.split()[1]
                self.kernels.append(Kernel(index, k, p))
                index += 1
                continue

    def range_check(self, index):
        if index < 0 or index >= len(self.kernels):
            raise IndexError, "%d is out of range (0-%d valid)" % (index, len(self.kernels)-1)
        return index

    def getindex(self):
        for i,k in enumerate(self.kernels):
            print("%2d: %s" % (i, k.description, k.path))
        index = int(raw_input("Select kernel to boot: "))
        return self.range_check(index)

    def boot_once(self, index):
        p = subprocess.Popen(["/sbin/grub", "--batch"], stdin=subprocess.PIPE)
        p.stdin.write("savedefault --default=%d --once\n" % index)
        p.stdin.close()
        ret = p.wait()
        if ret:
            raise RuntimeError, "call to grub failed! (%d)" % ret
        subprocess.call("reboot", shell=True)


class Grub2(object):
    def __init__(self):

        # make sure grub is configured properly
        for l in open("/etc/default/grub", "r"):
            l = l.strip()
            if l.startswith('GRUB_DEFAULT'):
                if l.split('=')[1].strip() != "saved":
                    raise RuntimeError, "Cannot do onetime boot! (set GRUB_DEFAULT=saved in /etc/default/grub)"

        self.kernels = []
        index = 0
        path = "/etc/grub2-efi.cfg"
        if not os.path.exists(path):
            path = "/etc/grub2.cfg"
        if not os.path.exists(path):
            raise RuntimeError, "No /etc/grub2-*.cfg file found!"

        for l in open(path):
            l = l.strip()
            if l.startswith("menuentry "):
                k = l[11:l.find('--class') - 2]
                continue
            if l.startswith('linux'):
                p = l.split()[1]
                self.kernels.append(Kernel(index, k, p))
                index += 1
                continue

    def range_check(self, index):
        if index < 0 or index >= len(self.kernels):
            raise IndexError, "%d is out of range (0-%d valid)" % (index, len(self.kernels)-1)
        return index

    def getindex(self):
        for k in self.kernels:
            print("%2d: %s: %s" % (k.index, k.description, k.path))
        index = int(raw_input("Select kernel to boot: "))
        return self.range_check(index)

    def boot_once(self, index):
        try:
            k = self.kernels[index]
        except IndexError as e:
            print("index %d is not a valid grub menu index!")
            raise
        subprocess.call("/sbin/grub2-reboot '%s'" % k.description, shell=True)
        subprocess.call("/sbin/grub2-mkconfig -o /tmp/grub2.cfg", shell=True)
        subprocess.call("reboot", shell=True)


def get_grub_version():
    p = subprocess.Popen(['rpm',  '-q', 'grub'], stdout=subprocess.PIPE)
    out = p.stdout.readline()
    if out.find("not installed") != -1:
        return 2
    return 1

if __name__ == "__main__":

    if os.getuid() != 0:
        raise RuntimeError, "must be root!"

    grubversion = get_grub_version()
    if grubversion == 1:
        grub = Grub1()
    else:
        grub = Grub2()

    try:
        index = int(sys.argv[1])
    except:
        index = grub.getindex()

    grub.boot_once(index)
