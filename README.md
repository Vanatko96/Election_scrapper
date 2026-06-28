# Election Scraper

This project scrapes the 2017 Czech parliamentary election results
from volby.cz for a chosen district. For every municipality in the
district it collects voter turnout and party votes, and saves them
into a single CSV file.

## Installation

Create and activate a virtual environment, then install the
required libraries:

python -m venv venv

venv\Scripts\Activate.ps1

pip install -r requirements.txt

# Usage

The program takes two arguments — the URL of a district and the name
of the output file:

python main.py <district_URL> <output_file.csv>

## Finding the district URL

The first argument must be a district listing page (a "ps32" URL
showing a list of municipalities). To find it:

1. Open https://www.volby.cz/pls/ps2017nss/ps3?xjazyk=CZ
2. Pick a region (kraj).
3. In the district table, click the "X" symbol in the
   "Výběr okrsku" column for the district you want.
4. You are now on the municipality list page — copy this URL.

A valid URL contains "ps32" and shows many municipalities. Do not
use a "ps311" detail page (a single municipality) — the program
reads those automatically.

## Example

A concrete example for the district of Prostějov:

python main.py "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=12&xnumnuts=7103" "results_prostejov.csv"

While running, the program prints its progress:

Processing: Alojzov
Processing: Bedihošť
Processing: Bílovice-Lutotín

...

Saved 97 municipalities to results_prostejov.csv

The output CSV contains one row per municipality: code, name,
registered voters, envelopes, valid votes, and a column for each
candidate party.

