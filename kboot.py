#!/usr/bin/python -tt
#
# script to selectively boot one grub entry *one time* and not
# affect the default boot entry
#
#  Copyright 2016 Clark Williams <williams@redhat.com>

import os
import sys
import os.path
import subprocess

# class for grub entries
class Kernel(object):
    __slots__ = ('index', 'description', 'path', 'isrt')
    def __init__(self, index, desc, path, isrt=False):
        self.index = index
        self.description = desc
        self.path = path
        self.isrt = isrt

# base class for both Grub1 and Grub2
class GrubBase(object):
    def __init__(self):
        self.kernels = []
        self.default_idx = -1

    # verify that a user-input index is valid
    def range_check(self, index):
        if index < 0 or index >= len(self.kernels):
            raise IndexError, "%d is out of range (0-%d valid)" % (index, len(self.kernels)-1)
        return index

    # grab an input from the user
    def getindex(self):
        index = raw_input("Select kernel to boot [%d]: " % self.default_idx)
        if index == '':
            index = self.default_idx
        index = int(index)
        return self.range_check(index)

    def reboot(self):
        print("rebooting")
        subprocess.call("reboot", shell=True)

    # return true if the selected path is a realtime kernel
    def isrt(self, path):
        if path.find(".rt") != -1:
            return True
        if path.find("-rt") != -1:
            return True
        return False

    # display available kernels
    def showkernels(self):
        for i,k in enumerate(self.kernels):
            if i == self.default_idx:
                output = "*"
            else:
                output = " "
            if k.isrt:
                output += "r %2d: %s" % (i, k.description)
            else:
                output += "  %2d: %s" % (i, k.description)
            print output


# deal with an installed Grub1 (RHEL6 and before)
class Grub1(GrubBase):
    def __init__(self):
        GrubBase.__init__(self)
        index = 0
        for l in open('/etc/grub.conf'):
            l = l.strip()
            if l.startswith('title'):
                k = l[6:-1]
                continue
            if l.startswith('kernel'):
                p = l.split()[1]
                self.kernels.append(Kernel(index, k, p, self.isrt(p)))
                index += 1
                continue
            if l.startswith('default'):
                self.default_idx = int(l.split('=')[1])

    def boot_once(self, index):
        if index != self.default_idx:
            p = subprocess.Popen(["/sbin/grub", "--batch"], stdin=subprocess.PIPE)
            p.stdin.write("savedefault --default=%d --once\n" % index)
            p.stdin.close()
            ret = p.wait()
            if ret:
                raise RuntimeError, "call to grub failed! (%d)" % ret
        self.reboot()

# deal with installed Grub2
class Grub2(GrubBase):
    def __init__(self):
        GrubBase.__init__(self)

        # make sure grub is configured properly
        for l in open("/etc/default/grub", "r"):
            l = l.strip()
            if l.startswith('GRUB_DEFAULT'):
                if l.split('=')[1].strip() != "saved":
                    raise RuntimeError, "Cannot do onetime boot! (set GRUB_DEFAULT=saved in /etc/default/grub)"

        saved_entry=""
        p = subprocess.Popen("grub2-editenv list", shell=True, stdout=subprocess.PIPE)
        for l in p.stdout.readlines():
            l = l.strip()
            if l.startswith("saved_entry"):
                saved_entry=l.split('=')[1]
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
                self.kernels.append(Kernel(index, k, p, self.isrt(p)))
                if k == saved_entry:
                    self.default_idx = index
                index += 1
                continue

    def boot_once(self, index):
        if index != self.default_idx:
            try:
                k = self.kernels[index]
            except IndexError as e:
                print("index %d is not a valid grub menu index!")
                raise
            subprocess.call("/sbin/grub2-reboot '%s'" % k.description, shell=True)
            subprocess.call("/sbin/grub2-mkconfig -o /tmp/grub2.cfg", shell=True)
        self.reboot()

# figure out what grub we have installed
def get_grub_version():
    p = subprocess.Popen(['rpm',  '-q', 'grub'], stdout=subprocess.PIPE)
    out = p.stdout.readline()
    if out.find("not installed") != -1:
        return 2
    return 1

#
# main logic
#
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
        grub.showkernels()
        index = grub.getindex()

    grub.boot_once(index)
