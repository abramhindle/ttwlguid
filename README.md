# Tiny Tina's Wonderlands Savefile GUID Changer and Renamer

To duplicate your build savefile you need to change the GUID of the file, otherwise it is ignored.

This script doesn't know much about the savefile, but it knows there's some kind of protobuffer in there.

It can read the protobuffer, but it can't write to it very well, so I instead opt to the directly modify the binary protobug data instead of re-encoding the protobuffer.

```
usage: ttwlguid.py [-h] [-i I] [-o O] [--name NAME] [--rename RENAME]
                   [--debug]

Tiny Tina's Wonderlands Savefile GUID Changer and Renamer

optional arguments:
  -h, --help       show this help message and exit
  -i I             Savefile as input
  -o O             Output Save File
  --name NAME      The current name of your character to replace
  --rename RENAME  The name to change your character to -- without this option
                   the character will be renamed based on original name and
                   GUID
  --debug          Enable debugging output
```

```
@slate:~/projects/ttwlguid$ python3 ttwlguid.py -i 2.sav --name StabbyFunnt --rename CoolFunnt -o CoolFunnt.sav
Loading 2.sav
decoding
1: 2
2: 637849703161310000
3: 169397
23: bytearray(b'0744E50B40DFEF680FE7348F322C4934')
43: {'10': {}, '12': 8389764605810401890}
bytearray(b'0744E50B40DFEF680FE7348F322C4934') -> bytearray(b'E85138E2EEEE40A7907C502E53C606C3')
Replacing Name bytearray(b'StabbyFunnt') with bytearray(b'CoolFunnt51')
Writing CoolFunnt.sav
```

# Dependencies

* blackboxprotobuf `pip3 install --user blackboxprotobuf`
