# FAT32-reader
Implementation of navigational and reading functionalities of a FAT32 file

The following functionalities have been implemented.


• stat <FILE_NAME/DIR_NAME>
Description: prints the size of the file or directory name, the attributes of the file or directory name,
and the first cluster number of the file or directory name if it is in the present working directory.
Return an error if FILE_NAME/DIR_NAME does not exist. (Note: The size of a directory will
always be zero.)

• cd <DIR_NAME>
Description: changes the present working directory to DIR_NAME. In other words, you need to
seek to the directory block.

• ls
Description: lists the contents of the current directory, including the “.” (here) and “..” (up one
directory) directories (if they are there). It should not list deleted files or system volume names.

• read FILE_NAME POSITION NUM_BYTES
Description: reads from a file named FILE_NAME, starting at POSITION, and prints
NUM_BYTES. Return an error when trying to read a directory.

• volume
Description: prints the volume name of the file system image. If there is a volume name, it will be
found in the root directory. If there is no volume name, it print the message “Error: volume name
not found.”

• deleted
Description: Finds and prints all the deleted files in the current directory. (It should act just like the
ls command, but only print the names of deleted files instead.)

• quit
Description: Quits the utility.
