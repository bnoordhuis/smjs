# smjs - gypified spidermonkey

Why? Because we like - nay, love - everything from the
[genus Ateles](https://github.com/creationix/luvmonkey)!

## Prerequisites

* Linux, OS X or Windows
* gcc 4.x or msvc 2010
* [gyp](https://github.com/bnoordhuis/gyp) (make sure it's on your path)

## How to build on UNIX

    ./configure
    make -j <num-cpus> V=1 BUILDTYPE=Release

## How to build on Windows

    vcbuild.bat

## Maintainer's note

Here is how the directories map onto mozilla-central.

    src/           => js/src/
    extra/js/      => js/public/
    extra/mozilla/ => mfbt/
