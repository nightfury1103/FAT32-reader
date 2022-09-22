"""

author      : Rishabh Dalal
file        : fat32_reader.py
description : fat32 reader

"""

import struct
import sys
import math


def get_bytes(f, pos, numBytes):
    
    f.seek(pos)
    data = f.read(numBytes)
    if (numBytes == 2):
        formatString = 'H'
    elif (numBytes == 1):
        formatString = 'B'
    elif (numBytes == 4):
        formatString = "i"
    else:
        raise Exception("not implemented")
    return struct.unpack(ENDIAN_FORMAT + formatString, data)[0] if data else 0

def info():
    
    print("BPB_BytesPerSec is ", hex(BPB_BytesPerSec), BPB_BytesPerSec)
    print("BPB_SecPerClus is " , hex(BPB_SecPerClus) , BPB_SecPerClus)
    print("BPB_RsvdsSecCnt is ", hex(BPB_RsvdsSecCnt), BPB_RsvdsSecCnt)
    print("BPB_NumFATs is "    , hex(BPB_NumFATs)    , BPB_NumFATs)
    print("BPB_FATSz32 is "    , hex(BPB_FATSz32)    , BPB_FATSz32)
    print("BPB_RootAddr is"    , hex(BPB_RootAddr)   , BPB_RootAddr)
    
    return True

def get_string(f, offset, size):

    f.seek(offset)
    d = f.read(size)
    if size != 1:
        return struct.unpack(f'{str(size)}s', d)[0]
    v = struct.unpack(f'{str(size)}c', d)
    return v[0] if v else ''

def ThisFATSecNum(N):
    return (BPB_RsvdsSecCnt + ((N*4)//BPB_BytesPerSec))

def ThisFATEntOffset(N):
    return ((N*4)% BPB_BytesPerSec)

def firstSectorOfCluster(n):
    rootDirSectors = ((BPB_RootEntCnt * 32) + ( BPB_BytesPerSec -1)) //  BPB_BytesPerSec
    firstDataSector = BPB_RsvdsSecCnt + (BPB_NumFATs *  BPB_FATSz32) + rootDirSectors
    return (n-2)*BPB_SecPerClus + firstDataSector

def firstSectorFromBase(n):
    firstDataSector = BPB_RsvdsSecCnt + (BPB_NumFATs *  BPB_FATSz32) + 0
    return (n-2)*BPB_SecPerClus + firstDataSector


def stat_helper(file_name):
    files = []
    status = stop = 1
    nxtCluster = currentClus
    
    while nxtCluster < int('0xFFFFFFF8', 16) and nxtCluster < 0xFFFFFF8:
        ##while loop chooses the cluster
        
        directory_address = firstSectorOfCluster(nxtCluster)*512

        for i in range(16):
            ## Processing one cluster
            
            status = get_bytes(f, (directory_address+32*i)+11, 1)

            name = clean_name(get_string(f, directory_address+32*i, 11))

            if status == 0x01:
                print("Attribute: ATTR_READ_ONLY")
                    
            elif status == 0x02:
                print("Attribute: ATTR_HIDDEN")
                    
            elif status == 0x04:
                print("Attribute: ATTR_SYSTEM")
                    
            elif status == 0x08:
                print("Attribute: ATTR_VOLUME_ID")
                    
            elif status == 0x10:
                print("Attribute: ATTR_DIRECTORY")
                    
            elif status == 0x20:
                print("Attribute: ATTR_ARCHIVE")

            size = get_bytes(f, (directory_address+32*i)+28, 4)
            high_clus = get_bytes(f, (directory_address+32*i)+28+20, 2)
            low_clus = get_bytes(f, (directory_address+32*i)+28+26,2)
            nxt  =  (high_clus << 16) + low_clus
            print('Size:', size)
            print('Next cluster number is:', hex(nxt))
            return

        ##Getting the address of next cluster
        next_fat_addr = (ThisFATSecNum(nxtCluster)*512) + ThisFATEntOffset(nxtCluster)
        nxtCluster = get_bytes(f, next_fat_addr, 4)
    print("Error: Directory/File '" + file_name + "' does not exist")


def cd_helper(drc):
    global currentClus
    files = []
    nxtCluster = currentClus
    
    while nxtCluster < int('0xFFFFFFF8', 16) and nxtCluster < 0xFFFFFF8:
        ##while loop chooses the cluster
        
        directory_address = firstSectorOfCluster(nxtCluster)*512

        for i in range(16):
            ## Processing one cluster
            
            line = get_string(f, directory_address+32*i, 11)
            status = get_bytes(f, directory_address+ (32*i) +11, 1)

            if status == 0x10:
                name = clean_name(line)
                if name == drc:
                    if drc == '..':
                        if abs_path:
                            abs_path.pop()
                    elif drc != '.':
                        abs_path.append(drc)
                    high_clus = get_bytes(f, (directory_address+32*i)+20, 2)
                    low_clus = get_bytes(f, (directory_address+32*i)+26,2)
                    val =  (high_clus << 16) + low_clus
                    if val == 0:
                        val = 2
                    
                    currentClus = val
                    return
            
            elif status == 0x20:
                name = clean_name(line)
                if name == drc:
                    print("Error: '" + drc + "' is a file, not a directory")
                    return

        ##Getting the address of next cluster
        next_fat_addr = (ThisFATSecNum(nxtCluster)*512) + ThisFATEntOffset(nxtCluster)
        nxtCluster = get_bytes(f, next_fat_addr, 4)
        
    print("Error: Directory '" + drc + "' does not exist")


def read_helper(filename, l, r):
    
    nxtCluster = currentClus
    
    while nxtCluster < int('0xFFFFFFF8', 16) and nxtCluster < 0xFFFFFF8:
    
        directory_address = firstSectorOfCluster(nxtCluster)*512
        
        for i in range(16):
            line = get_string(f, directory_address+32*i, 11)
            status = get_bytes(f, directory_address+ (32*i) +11, 1)

            if status == 0x20: 
                line = clean_name(line.strip())
                if line == filename:
                    high_clus = get_bytes(f, directory_address + (32*i)+20, 2)
                    low_clus = get_bytes(f, directory_address + (32*i)+26,2)
                
                    tmp =  (high_clus << 16) + low_clus
                    first_sector = firstSectorFromBase(tmp)*BPB_BytesPerSec
                    data = get_string(f, first_sector+int(l), int(r))
                    data = data.decode('latin-1')
                    print(data)
                    return
                
            elif status == 0x10:
                line = clean_name(line.strip())
                if line == filename:
                    print('Error: Cannot read a directory')
                    return
            
            f.seek(directory_address+32*i, 0)
        
        next_fat_addr = (ThisFATSecNum(nxtCluster)*512) + ThisFATEntOffset(nxtCluster)
        nxtCluster = get_bytes(f, next_fat_addr, 4)

    print("Error: file '" + filename + "' does not exist")
    
def deleted_helper():
    files = []
    nxtCluster = currentClus

    while nxtCluster < int('0xFFFFFFF8', 16) and nxtCluster < 0xFFFFFF8:

        directory_address = firstSectorOfCluster(nxtCluster)*512

        for i in range(16):
            line = get_string(f, directory_address+32*i, 11)
            status = get_bytes(f, directory_address+ (32*i) +11, 1)
            if status in [0x10, 0x20]:
                try:
                    line.strip().decode('utf-8')
                except:
                    line = line.strip().decode('latin-1')
                    if ' ' in line:
                        l = line.split()
                        line = '.'.join(l)
                    files.append(f'_{line}')

            else:
                files.append('')
            f.seek(directory_address+32*i, 0)

        next_fat_addr = (ThisFATSecNum(nxtCluster)*512) + ThisFATEntOffset(nxtCluster)
        nxtCluster = get_bytes(f, next_fat_addr, 4)

    for i in files:
        if i:
            print(i, end='    ')
    print()
    
def ls_helper():
    files = []

    nxtCluster = currentClus
    rootList = []

    while nxtCluster < int('0xFFFFFFF8', 16) and nxtCluster < 0xFFFFFF8:

        directory_address = firstSectorOfCluster(nxtCluster)*512

        for i in range(16):
            line = get_string(f, directory_address+32*i, 11)
            status = get_bytes(f, directory_address+ (32*i) +11, 1)
            if status in [0x10, 0x20]:
                line = clean_name(line.strip())            
                files.append(line)
            else:
                files.append('')
            rootList.append(directory_address + 32*i)
            f.seek(directory_address+32*i, 0)

        next_fat_addr = (ThisFATSecNum(nxtCluster)*512) + ThisFATEntOffset(nxtCluster)
        nxtCluster = get_bytes(f, next_fat_addr, 4)

    for i in files:
        if i:
            print(i, end='    ')
    print()
    
def clean_name(name):
    try:
        name = name.decode('utf-8')
    except:
        return ''

    if name:
        l = name.split()
        l = '.'.join(l)
        return l
    return ''
    
def main():
    ##main driver code

    global BPB_BytesPerSec
    global BPB_SecPerClus
    global BPB_RsvdsSecCnt
    global BPB_NumFATs
    global BPB_FATSz32
    global BPB_FATSzRootEntCnt
    global BPB_RootClus
    global ENDIAN_FORMAT
    global BPB_RootAddr
    global currentClus
    global BPB_RootEntCnt
    global f
    global abs_path

    f = open("fat32.img", 'rb')
    ENDIAN_FORMAT = '<' if sys.byteorder == 'little' else '>'
    abs_path = []
    BPB_BytesPerSec = get_bytes(f, 11, 2)
    BPB_SecPerClus  = get_bytes(f, 13, 1)
    BPB_RsvdsSecCnt = get_bytes(f, 14, 2)
    BPB_NumFATs     = get_bytes(f, 16, 1)
    BPB_FATSz32     = get_bytes(f, 36, 4)
    BPB_RootEntCnt = 0

    BPB_RootClus = str(get_bytes(f, 44, 4))

    rootDirSectors = ((BPB_RootEntCnt * 32) + ( BPB_BytesPerSec -1)) //  BPB_BytesPerSec
    firstDataSector = BPB_RsvdsSecCnt + (BPB_NumFATs *  BPB_FATSz32) + rootDirSectors

    BPB_RootAddr = 512*((( int(BPB_RootClus)-2)* BPB_SecPerClus) + firstDataSector)
    currentClus = get_bytes(f, 44, 2)

    while True:
        print()
        path = '/' + '/'.join(abs_path)
        user_input = input(f"{path}] ")
        user_input_list = user_input.split()
        command = user_input_list[0].strip()
        args = user_input_list[1:]

        if command == 'info':
            info()

        elif command == 'volume':
            vol = get_string(f, BPB_RootAddr, 11)
            vol = vol.strip().decode("utf-8")
            if vol != '' and vol:
                print(vol)
            else:
                print("Error: Volume name not found")

        elif command == 'stat':
            stat_helper(args[0])

        elif command == 'ls':
            ls_helper()

        elif command == 'deleted':
            deleted_helper()

        elif command == 'read':
            read_helper(args[0], args[1], args[2])

        elif command == 'cd':
            cd_helper(args[0])

        elif command == 'quit':
            print('Quitting')
            f.close()
            quit()

        else:
            print('Unrecognized command')
main()
