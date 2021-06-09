# GitHub summary generator

## Installation

clone the repository or download the source code!
Afterwards be sure to have the dependencies installed by calling `pip install -r requirements.txt` in the source folder.
Of course you need to have python installed!

## Use

basic execution: `python generator.py <username>`

parameters:
- `-i, --intervall`: Sets intervall. `YEAR` or `MONTH`, default is year
- `-e, --endtime`: Sets endpoint. `TODAY` or specific datetime int e.g. `64853273685726`, default is today

The generator will put a .tex file in the output folder.
This could be converted to a pdf by using e.g [MiKTex](https://miktex.org/), [Overleaf](https://de.overleaf.com/), [latexbase](https://latexbase.com/), etc.

## Known issues


## Further information

Used api: [https://api.github.com](https://api.github.com)