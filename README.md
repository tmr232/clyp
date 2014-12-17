clyp
====

clyp is a command line tool for interacting with the clipboard.

It can copy/paste directly in the command-line.

Usage
-----

Simple copy

    clyp This text will be copied
    
Simple paste

    clyp
    
Copy from pipe

    echo This text will be copied | clyp
    
Paste to pipe

    clyp | more
    
Copy-thruogh

    echo This will get copied and piped | clyp | more
    

Enjoy!