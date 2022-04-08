#!/usr/bin/env python3
# originally was https://github.com/apocalyptech/bl3-cli-saveedit/blob/master/bl3save/bl3save.py
# Copyright (c) 2020-2021 CJ Kucera (cj@apocalyptech.com)
# 
# This software is provided 'as-is', without any express or implied warranty.
# In no event will the authors be held liable for any damages arising from
# the use of this software.
# 
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
# 
# 1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software in a
#    product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
# 
# 2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
# 
# 3. This notice may not be removed or altered from any source distribution.

# The encryption/decryption stanzas in BL3Save.__init__ and BL3Save.save_to
# were helpfully provided by Gibbed (rick 'at' gibbed 'dot' us), so many
# thanks for that!  https://twitter.com/gibbed/status/1246863435868049410?s=19
#
# The rest of the savegame format was gleaned from 13xforever/Ilya's
# "gvas-converter" project: https://github.com/13xforever/gvas-converter

import struct
import uuid

class BL3Save(object):
    """
    Real simple wrapper for a BL3 savegame file.
    
    Only tested on PC versions.  Thanks to Gibbed for the encryption method and
    the Protobuf definitions!
    https://twitter.com/gibbed/status/1246863435868049410?s=19
    All these getters/setters are rather un-Pythonic; should be using
    some decorations for that instead.  Alas!
    """

    _prefix_magic = bytearray([
        0x71, 0x34, 0x36, 0xB3, 0x56, 0x63, 0x25, 0x5F,
        0xEA, 0xE2, 0x83, 0x73, 0xF4, 0x98, 0xB8, 0x18,
        0x2E, 0xE5, 0x42, 0x2E, 0x50, 0xA2, 0x0F, 0x49,
        0x87, 0x24, 0xE6, 0x65, 0x9A, 0xF0, 0x7C, 0xD7,
        ])

    _xor_magic = bytearray([
        0x7C, 0x07, 0x69, 0x83, 0x31, 0x7E, 0x0C, 0x82,
        0x5F, 0x2E, 0x36, 0x7F, 0x76, 0xB4, 0xA2, 0x71,
        0x38, 0x2B, 0x6E, 0x87, 0x39, 0x05, 0x02, 0xC6,
        0xCD, 0xD8, 0xB1, 0xCC, 0xA1, 0x33, 0xF9, 0xB6,
        ])

    def __init__(self, filename, debug=False):
        self.filename = filename
        with open(filename, 'rb') as df:

            header = df.read(4)
            assert(header == b'GVAS')

            self.sg_version = self._read_int(df)
            if debug:
                print('Savegame version: {}'.format(self.sg_version))
            self.pkg_version = self._read_int(df)
            if debug:
                print('Package version: {}'.format(self.pkg_version))
            self.engine_major = self._read_short(df)
            self.engine_minor = self._read_short(df)
            self.engine_patch = self._read_short(df)
            self.engine_build = self._read_int(df)
            if debug:
                print('Engine version: {}.{}.{}.{}'.format(
                    self.engine_major,
                    self.engine_minor,
                    self.engine_patch,
                    self.engine_build,
                    ))
            self.build_id = self._read_str(df)
            if debug:
                print('Build ID: {}'.format(self.build_id))
            self.fmt_version = self._read_int(df)
            if debug:
                print('Custom Format Version: {}'.format(self.fmt_version))
            fmt_count = self._read_int(df)
            if debug:
                print('Custom Format Data Count: {}'.format(fmt_count))
            self.custom_format_data = []
            for _ in range(fmt_count):
                guid = self._read_guid(df)
                entry = self._read_int(df)
                if debug:
                    print(' - GUID {}: {}'.format(guid, entry))
                self.custom_format_data.append((guid, entry))
            self.sg_type = self._read_str(df)
            if debug:
                print('Savegame type: {}'.format(self.sg_type))

            # Read in the actual data
            remaining_data_len = self._read_int(df)
            data = bytearray(df.read(remaining_data_len))

            # Decrypt
            for i in range(len(data)-1, -1, -1):
                if i < 32:
                    b = BL3Save._prefix_magic[i]
                else:
                    b = data[i - 32]
                b ^= BL3Save._xor_magic[i % 32]
                data[i] ^= b
            self.data = data
            # Make sure that was all there was
            last = df.read()
            assert(len(last) == 0)

    def save_to(self, filename):
        """
        Saves ourselves to a new filename
        """
        with open(filename, 'wb') as df:

            # Header info
            df.write(b'GVAS')
            self._write_int(df, self.sg_version)
            self._write_int(df, self.pkg_version)
            self._write_short(df, self.engine_major)
            self._write_short(df, self.engine_minor)
            self._write_short(df, self.engine_patch)
            self._write_int(df, self.engine_build)
            self._write_str(df, self.build_id)
            self._write_int(df, self.fmt_version)
            self._write_int(df, len(self.custom_format_data))
            for guid, entry in self.custom_format_data:
                self._write_guid(df, guid)
                self._write_int(df, entry)
            self._write_str(df, self.sg_type)

            # Turn our parsed protobuf back into data
            data = self.data # bytearray?

            # Encrypt
            for i in range(len(data)):
                if i < 32:
                    b = self._prefix_magic[i]
                else:
                    b = data[i - 32]
                b ^= self._xor_magic[i % 32]
                data[i] ^= b

            # Write out to the file
            self._write_int(df, len(data))
            df.write(data)

    def _read_int(self, df):
        return struct.unpack('<I', df.read(4))[0]

    def _write_int(self, df, value):
        df.write(struct.pack('<I', value))

    def _read_short(self, df):
        return struct.unpack('<H', df.read(2))[0]

    def _write_short(self, df, value):
        df.write(struct.pack('<H', value))

    def _read_str(self, df):
        datalen = self._read_int(df)
        if datalen == 0:
            return None
        elif datalen == 1:
            return ''
        else:
            value = df.read(datalen)
            return value[:-1].decode('utf-8')

    def _write_str(self, df, value):
        if value is None:
            self._write_int(df, 0)
        elif value == '':
            self._write_int(df, 1)
        else:
            data = value.encode('utf-8') + b'\0'
            self._write_int(df, len(data))
            df.write(data)

    def _read_guid(self, df):
        data = df.read(16)
        return data
        # A bit silly to bother formatting it, since we don't care.
        #arr = ''.join(['{:02x}'.format(d) for d in data])
        #return '{}-{}-{}-{}-{}'.format(
        #        arr[0:8],
        #        arr[8:12],
        #        arr[12:16],
        #        arr[16:20],
        #        arr[20:32],
        #        )

    def _write_guid(self, df, value):
        df.write(value)

def replace_value_in_bytearray(b,v,r):
    assert(len(v) == len(r))
    newdata = b.copy()
    found = False
    for i in range(len(newdata)):
        if newdata[i:i+len(v)] == v:
            newdata[i:i+len(v)] = r
            found = True
            break
    if not found:
        raise Exception(f"Did not find the string {v}")
    return newdata

if __name__ == "__main__":
    # filename = "wonderlands.sav"
    filename = "5.sav"
    import sys
    if len(sys.argv)>1:
        filename = sys.argv[1]
    # filename = "blister-amara.bl3.sav"
    print(f"Loading {filename}")
    bl3save = BL3Save(filename, debug=True)
    print(bl3save.sg_version)
    print(bl3save.pkg_version)
    print(bl3save.engine_major)
    print(bl3save.engine_minor)
    print(bl3save.engine_patch)
    print(bl3save.engine_build)
    print(bl3save.build_id)
    print(bl3save.fmt_version)
    print(len(bl3save.custom_format_data))
    for guid, entry in bl3save.custom_format_data:
        print(f'guid:{guid} entry:{entry}')
    print(bl3save.sg_type)
    print(len(bl3save.data))
    with open("bl3save.proto",'wb') as fd:
        fd.write(bl3save.data)
    # print(bl3save.data)
    # from google.protobuf.json_format import MessageToJson
    # print( MessageToJson(bl3save.data) )
    # print( MessageToJson(bl3save.data[32:]) )
    import blackboxprotobuf
    #message,typedef = blackboxprotobuf.protobuf_to_json(bl3save.data)
    #print(typedef)
    #print(message)
    print("decoding")
    message,typedef = blackboxprotobuf.decode_message(bl3save.data)
    for i in ["1","2","3","23","43"]:
        print(f'{i}: {message[str(i)]}')
    GUID = message["23"] # protoc --decode_raw
    NEWGUID = bytearray(uuid.uuid4().hex.upper(),'ascii')
    print(f'{GUID} -> {NEWGUID}')
    NAME = None
    NAME = 'StabbyFunnt'
    # having problems finding the name
    # Assign the prefix of the GUID there
    # NAME = message["43"] # protoc --decode_raw
    #print(f"GUID: {GUID} NAME {NAME}")
    # NEWNAME = NAME.copy()    
    #if len(NEWNAME) > 4:
    #    NEWNAME[-4:] = NEWGUID[0:4]
    #for k in message.keys():
    #    print(f'{k} {message[k]}')
    # now search for it and change it.
    newdata = replace_value_in_bytearray(bl3save.data, GUID,NEWGUID)
    if NAME is not None:
        if type(NAME) is str:            
            NAME = bytearray(NAME,'ascii')
        assert(type(NAME) is bytearray)
        newname = NAME.copy()    
        if len(newname) > 4:
            newname[-4:] = NEWGUID[0:4]
        newdata = replace_value_in_bytearray(newdata, NAME,newname)
        

    bl3save.save_to(filename+".old_guid.sav")
    bl3save.data = newdata
    bl3save.save_to(filename+".new_guid.sav")
    #         
    # 
    # print("Modifying")
    # message["1"] = 10
    # message["2"] = 699999999999999999
    # message["3"] = 19999
    # print("encoding")
    # data = blackboxprotobuf.encode_message(message,typedef)
    # # print(data)
    # with open("bl3save.proto.modify",'wb') as fd:
    #     fd.write(data)
