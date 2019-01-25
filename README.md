# BuyKim
*A script to automate Kimsufi (and other OVH servers) purchase*

# Rationale
Recently I wanted to purchase a Kimsufi server. However, I was not
the only one to want one and OVH has no queuing mechanim, leaving
me the only option of reloading the availability page waiting for an
opportunity to rent one.

Pretty quickly, I came up with this script: an **automated tool** to
purchase your favorite Kimsufi model as soon as it is available without
wasting your precious time waiting!

# Usage

- Install requirements: `pip install -r requirements.txt`

- One of the dependency is `Selenium` that depends on drivers: https://github.com/SeleniumHQ/selenium/blob/master/py/docs/source/index.rst#user-content-drivers.

On Mac to make this step easier, run:
```
brew install geckodriver
```

- Connect your OVH account to PayPal (this seemed the best option to avoid handling Credit Card data, but PR welcome if you want to do otherwise!)

- Run `python buyKim.py`
```
$ python buyKim.py --help
Usage: buyKim.py [OPTIONS]

Options:
  -t, --timeout-conn INTEGER  Maximum time in seconds to wait for webservice
                              answer.  [default: 5]
  -i, --interval FLOAT        Minimum interval in seconds between two requests
                              [default: 7.5]
  -f, --product-family TEXT   The family of servers (ie. "Kimsufi"/"So you
                              Start")  [default: Kimsufi]
  -p, --ref-product TEXT      Reference of the server (ie 1801sk12 for KS1,
                              1801sys29 for some soYouStart servers  [default:
                              1801sk12]
  -z, --ref-zones TEXT        Data center short name(s) (ie "-z gra -z rbx")
                              [default: gra, rbx, lon, fra]
  --ovh-user TEXT
  --ovh-pass TEXT
  --debug / --no-debug        Debug mode, disable by default. Add --debug flag
                              to enable
  --help                      Show this message and exit.
```

- Profit!

# Architecture

The script is split in two parts:  

- The first part uses `requests` to poll OVH's availability webservice,
and parses its response to find the product you want. When the response
describes your product as available, the second part of the script kicks in.
- The second part uses `selenium` for opening the listing page, then selects
your product, injects some Angular.JS-specific JavaScript for selecting your
datacenter, waits for PayPal to load, and clicks on Purchase!

# Contributing
Your contribution is welcome! Don't hesitate to report issues or give feedback
[using our Issue Tracker](https://github.com/PLNech/BuyKim/issues/new), and to propose features or bugfixes by [submitting a pull request](https://github.com/PLNech/BuyKim/compare).

# License

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
