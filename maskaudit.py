#!/usr/bin/python
#
# This file is Copyright (c) 2010 by the GPSD project
# BSD terms apply: see the file COPYING in the distribution root for details.
#
# With -p, dump a Python status mask list translated from the C one.
#
# With -c, generate C code to dump client-side masks for debugging purposes.
#
# With -d, generate C code to dump demon-side masks for debugging purposes.

import sys, commands, glob, getopt

class SourceExtractor:
    def __init__(self, sourcefile, suffix, clientside):
        self.sourcefile = sourcefile
        self.suffix = suffix
        self.clientside = clientside
        self.daemonfiles = ["gpsd.c", "libgpsd_core.c", "pseudonmea.c"] + glob.glob("driver_*.c") + ["gpsmon.c"] + glob.glob("monitor_*.c")
        self.masks = []
        self.primitive_masks = []
        for line in file(self.sourcefile):
            if line.startswith("#define") and self.suffix in line:
                fields = line.split()
                self.masks.append((fields[1], fields[2]))
                if fields[2].endswith("u"):
                    self.primitive_masks.append((fields[1], fields[2]))
    
    def in_library(self, flag):
        (status, output) = commands.getstatusoutput("grep %s libgps_core.c libgps_json.c gpsctl.c" % flag)
        return status == 0

    def in_daemon(self, flag):
        (status, output) = commands.getstatusoutput("grep %s %s" % (flag, " ".join(self.daemonfiles)))
        return status == 0

    def relevant(self, flag):
        if self.clientside:
            return self.in_library(flag)
        else:
            return self.in_daemon(flag)
    
if __name__ == '__main__':
    try:
        (options, arguments) = getopt.getopt(sys.argv[1:], "cdpt")
        pythonize = tabulate = False
        clientgen = daemongen = False
        for (switch, val) in options:
            if (switch == '-p'):
                pythonize = True
            if (switch == '-c'):
                clientgen = True
            if (switch == '-d'):
                daemongen = True
            if (switch == '-t'):
                tabulate = True

        if clientgen:
            source = SourceExtractor("./gps.h", "_SET", clientside=True)
            prefix = "gps"
            banner = "Library"
        elif daemongen:
            source = SourceExtractor("./gpsd.h", "_IS", clientside=False)
            prefix = "gpsd"
            banner = "Daemon"

        if tabulate:
            print "%-14s	%8s %8s" % (" ", "Library", banner)
            for (flag, value) in source.masks:
                print "%-14s	%8s" % (flag, source.relevant(flag))
        if pythonize:
            for (d, v) in source.masks:
                if v[-1] == 'u':
                    v = v[:-1]
                print "%-15s\t= %s" % (d, v)
        if not pythonize and not tabulate:
            maxout = 0
            for (d, v) in source.primitive_masks:
                if source.relevant(d):
                    stem = d
                    if stem.endswith(source.suffix):
                        stem = stem[:-len(source.suffix)]
                    maxout += len(stem) + 1
            print """/* This code is generated.  Do not hand-hack it! */
#include <stdio.h>
#include <string.h>

#include \"gpsd.h\"

const char *%s_maskdump(gps_mask_t set)
{
    static char buf[%d];
    const struct {
	gps_mask_t      mask;
	const char      *name;
    } *sp, names[] = {"""  % (prefix, maxout + 3,)
            for (flag, value) in source.primitive_masks:
                stem = flag
                if stem.endswith(source.suffix):
                    stem = stem[:-len(source.suffix)]
                print "\t{%s,\t\"%s\"}," % (flag, stem)
            print '''\
    };

    memset(buf, '\\0', sizeof(buf));
    buf[0] = '{';
    for (sp = names; sp < names + sizeof(names)/sizeof(names[0]); sp++)
	if ((set & sp->mask)!=0) {
	    (void)strlcat(buf, sp->name, sizeof(buf));
	    (void)strlcat(buf, "|", sizeof(buf));
	}
    if (buf[1] != \'\\0\')
	buf[strlen(buf)-1] = \'\\0\';
    (void)strlcat(buf, "}", sizeof(buf));
    return buf;
}
'''
    except KeyboardInterrupt:
        pass

# The following sets edit modes for GNU EMACS
# Local Variables:
# mode:python
# End:
