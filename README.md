# PyStowSafe

A python wrapper script for GNU `stow`.
Adds functionality to add files to stow packages and backup conflicts before executing stow.

## Requirements
`stow`:
- Can be installed as perl module via `capnm Stow` as user
  - `cpanm` can be installed in $HOME with:
    - `wget -O- http://cpanmin.us | perl - -l ~/perl5 App::cpanminus local::lib`
    -  `` eval `perl -I ~/perl5/lib/perl5 -Mlocal::lib` ``
