# GitHub summary generator

## Installation

clone the repository or download the source code!
Afterwards be sure to have the dependencies installed by calling `pip install -r requirements.txt` in the source folder.
Of course you need to have python installed!

## Use

basic execution: `python generator.py <username>`

parameters:
`-i, --intervall`: Sets intervall. `YEAR` or `MONTH`, default is year
`-e, --endtime`: Sets endpoint. `TODAY` or specific datetime int e.g. `64853273685726`, default is today

## Known issues

- Currently the generator does not verify whether or not a repo is in the given timerange. This means it will print out all repos...

## Further information

Used api: [https://api.github.com](https://api.github.com)