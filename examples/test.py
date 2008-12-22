#!/usr/bin/env python
#.awk '$0 ~ /case [0-9]+: .. 3/ { sys.stdout.write($2 }' src/dmidecode.c|tr ':\n' ', '

from pprint import pprint
import os, sys, random, tempfile, time
import commands

dmidecode = True in [os.path.exists(os.path.join(_, "dmidecode")) for _ in os.getenv("PATH").split(':')]
if dmidecode:
  print "Please install `dmidecode' (the binary) for complete testing."

FH, DUMP = tempfile.mkstemp()
os.unlink(DUMP)
os.close(FH)

total = 0
success = 0

def test(r):
  global total
  global success

  total += 1
  if r:
    sys.stdout.write("Good\n")
    success += 1
    return True
  else:
    sys.stdout.write("FAILED\n")
    return False

total += 1
print "-"*80
sys.stdout.write("Importing module...")
try:
  import dmidecode
  success += 1
  sys.stdout.write("Done\n")
  sys.stdout.write(" * Version: %s\n"%dmidecode.version)
  sys.stdout.write(" * DMI Version String: %s\n"%dmidecode.dmi)

  print "-"*80
  sys.stdout.write("Testing that default device is /dev/mem...")
  test(dmidecode.get_dev() == "/dev/mem")

  sys.stdout.write("Testing that write-lock will not break on dump()...")
  test(not dmidecode.dump())

  sys.stdout.write("Testing ability to change device to %s..."%DUMP)
  test(dmidecode.set_dev(DUMP))

  sys.stdout.write("Testing that device has changed to %s..."%DUMP)
  test(dmidecode.get_dev() == DUMP)

  sys.stdout.write("Testing that write on new file is ok...")
  test(dmidecode.dump())

  sys.stdout.write("Testing that file was actually written...")
  time.sleep(0.1)
  test(os.path.exists(DUMP))
  os.unlink(DUMP)

  types = range(0, 42)+range(126, 128)
  bad_types = [-1, -1000, 256]
  sections = ["bios", "system", "baseboard", "chassis", "processor", "memory", "cache", "connector", "slot"]
  devices = []
  if os.path.exists("private"):
    devices.extend([os.path.join("private", _) for _ in os.listdir("private")])
    devices.remove('private/.svn')
  else:
    sys.stdout.write("If you have memory dumps to test, create a directory called `private' and drop them in there.\n")
  devices.append("/dev/mem")
  random.shuffle(types)
  random.shuffle(devices)
  random.shuffle(sections)

  for dev in devices:
    sys.stdout.write(" * Testing %s..."%dev); sys.stdout.flush()
    if test(dmidecode.set_dev(dev) and dmidecode.get_dev() == dev):
      print "-"*80
      print sections
      for section in sections:
        sys.stdout.write("   * Testing %s..."%section); sys.stdout.flush()
        output = getattr(dmidecode, section)()
        test(output is not False)
        if output: sys.stdout.write("     * %s\n"%output.keys())

      print "-"*80
      for i in bad_types:
        sys.stdout.write("   * Testing bad type %i..."%i); sys.stdout.flush()
        try:
          output = dmidecode.type(i)
          test(output is False)
        except SystemError:
          sys.stdout.write("FAILED\n")

      print "-"*80
      for i in types:
        sys.stdout.write("   * Testing type %i..."%i); sys.stdout.flush()
        output = dmidecode.type(i)
        if dmidecode:
          _output = commands.getoutput("dmidecode -t %d"%i).strip().split('\n')
          test(len(_output) == 1 and len(output) == 0 or True)
        else:
          test(output is not False)
        if output:
          sys.stdout.write("     * %s\n"%output.keys())

except ImportError:
  sys.stdout.write("FAILED\n")

sys.stdout.write("Score: %d/%d\n"%(success, total))
