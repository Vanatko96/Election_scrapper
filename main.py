"""
main.py: Election scraper for the Chamber of Deputies 2017 results.

Scrapes per-municipality election results from volby.cz for a chosen
district and saves them into a CSV file. Run with two arguments:
the district URL and the output file name.

author: Lukáš Vaňátko
"""

import sys
import csv

import requests
from bs4 import BeautifulSoup


def check_arguments(args: list[str]) -> tuple[str, str]:
    """Validate the two command-line arguments (URL and output file name).

    Exits the program with a message if the number of arguments is wrong
    or the URL has an invalid format.
    Returns a tuple (url, output_file).
    """
    if len(args) != 3:
        sys.exit("Too few/many arguments.")

    url = args[1]
    output_file = args[2]

    # The district page must be a "ps32" listing, otherwise scraping fails.
    if not url.startswith("https://www.volby.cz/pls/ps2017nss/ps32"):
        sys.exit("Wrong URL.")

    return url, output_file


def get_soup(url: str) -> BeautifulSoup:
    """Download the page at the URL and return it as a BeautifulSoup object."""
    response = requests.get(url)
    return BeautifulSoup(response.text, "html.parser")


def parse_municipalities(soup: BeautifulSoup) -> list[dict]:
    """Extract the list of municipalities from the main district page.

    For each municipality returns a dict with its code, name and detail URL.
    """
    base = "https://www.volby.cz/pls/ps2017nss/"
    links = soup.find_all("a")
    municipalities = []

    # Each municipality links to a "ps311" detail page; the code links
    # have numeric text, which filters out the duplicate "X" links.
    municipalities_links = [
        a for a in links
        if a.get("href")
        and "ps311" in a.get("href")
        and a.get_text().isdigit()
    ]

    for a in municipalities_links:
        code = a.get_text(strip=True)
        href = a.get("href")
        # The municipality name is in a sibling cell of the same table row.
        # Name is the second cell; statutory cities (Liberec, Plzeň, ...)
        # lack the "overflow_name" class, so select by position instead.
        row = a.find_parent("tr")
        name = row.find_all("td")[1].get_text(strip=True)
        municipalities.append({
            "code": code,
            "name": name,
            "url": base + href,
        })

    return municipalities


def text_to_int(text: str) -> int:
    """Convert a number string with non-breaking spaces to an integer.

    Returns 0 for empty cells or a dash ('-') used on volby.cz
    where a party did not run in the given area.
    """
    # volby.cz uses non-breaking spaces as thousands separators.
    cleaned = text.replace("\xa0", "").replace(" ", "").strip()
    if cleaned in ("", "-"):
        return 0
    return int(cleaned)


def get_party_names(soup: BeautifulSoup) -> list[str]:
    """Extract the names of all candidate parties (for the CSV header)."""
    # Parties are split across two tables (t1 = left, t2 = right).
    name_cells = soup.find_all(
        "td", {"headers": ["t1sa1 t1sb2", "t2sa1 t2sb2"]}
    )
    names = [cell.get_text(strip=True) for cell in name_cells]
    if names and names[-1] == "-":
        names = names[:-1]
    return names


def parse_municipality_results(url: str) -> dict:
    """Extract voter stats and party votes from a single municipality page.

    Returns a dict with registered voters, envelopes, valid votes
    and votes for each party.
    """
    soup = get_soup(url)

    registered = text_to_int(soup.find("td", {"headers": "sa2"}).get_text())
    envelopes = text_to_int(soup.find("td", {"headers": "sa3"}).get_text())
    valid = text_to_int(soup.find("td", {"headers": "sa6"}).get_text())

    # The "sb3" part of the header selects vote counts, not percentages.
    vote_cells = soup.find_all(
        "td", {"headers": ["t1sa2 t1sb3", "t2sa2 t2sb3"]}
    )
    # Drop the trailing separator cell ('-') if present.
    if vote_cells and vote_cells[-1].get_text(strip=True) == "-":
        vote_cells = vote_cells[:-1]
    party_votes = [text_to_int(cell.get_text()) for cell in vote_cells]

    return {
        "registered": registered,
        "envelopes": envelopes,
        "valid": valid,
        "votes": party_votes,
    }


def build_header(party_names: list[str]) -> list[str]:
    """Build the CSV header: fixed columns plus all party names."""
    return ["code", "location", "registered", "envelopes", "valid"] + party_names


def write_csv(filename: str, header: list[str], rows: list[list]) -> None:
    """Write the header and municipality result rows to a CSV file."""
    # utf-8-sig keeps Czech diacritics readable in Excel.
    with open(filename, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def main() -> None:
    """Run the whole program: validate args, scrape data, write CSV."""
    url, output_file = check_arguments(sys.argv)
    soup = get_soup(url)
    municipalities = parse_municipalities(soup)

    # Party names are identical for every municipality, so read them once.
    party_names = get_party_names(get_soup(municipalities[0]["url"]))
    header = build_header(party_names)

    rows = []
    for municipality in municipalities:
        results = parse_municipality_results(municipality["url"])
        # Fixed columns first, then the party votes expanded into columns.
        row = [
            municipality["code"],
            municipality["name"],
            results["registered"],
            results["envelopes"],
            results["valid"],
        ] + results["votes"]
        rows.append(row)
        print(f"Processing: {municipality['name']}")

    write_csv(output_file, header, rows)
    print(f"Saved {len(rows)} municipalities to {output_file}")


if __name__ == "__main__":
    main()