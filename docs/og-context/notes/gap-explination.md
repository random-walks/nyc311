> Archived planning note: this analysis preserves the original `v0.1` framing.
> For the active release framing, use the main docs for the upcoming `0.2.0a1`
> alpha.

Yes: all three still look like **real gaps**, but only if you position them as
**end-to-end, reusable, NYC-specific tools** rather than generic wrappers around
existing libraries. The pattern I found is that there are plenty of **building
blocks** and a handful of **one-off research repos**, but I did **not** find a
clearly popular, maintained, `pip install`-style package that already delivers
the exact product shape you described for any of the three ideas
[cjio README](https://raw.githubusercontent.com/cityjson/cjio/develop/README.rst)
[CityTiler README](https://raw.githubusercontent.com/Jeremy-Gaillard/CityTiler/master/README.md)
[tsdataclinic/mta README](https://raw.githubusercontent.com/tsdataclinic/mta/master/README.md)
[smart-311 README](https://raw.githubusercontent.com/hersh-gupta/smart-311/main/README.md)
[nyc-311-analytics README](https://raw.githubusercontent.com/rajatrayaraddi/nyc-311-analytics/main/README.md).

## `nyc-mesh`

This one looks like the **cleanest gap** of the three. I found tools for
adjacent formats and conversions, but not a popular NYC-focused toolkit that
takes NYC open 3D data from raw inputs to lightweight web-ready outputs in the
way your spec describes
[cjio README](https://raw.githubusercontent.com/cityjson/cjio/develop/README.rst)
[CityTiler README](https://raw.githubusercontent.com/Jeremy-Gaillard/CityTiler/master/README.md)
[PyPI search results for CityGML/3D Tiles packages](https://pypi.org/project/cjio/).

The main incumbents are:

- `cjio`, which is a Python CLI/API for **CityJSON**, not an NYC-specific
  CityGML + LiDAR preparation pipeline; it supports things like reprojection,
  subset selection, validation, and glTF export, but it is format tooling rather
  than “download NYC data and produce deployable neighborhood outputs” product
  tooling
  [cjio README](https://raw.githubusercontent.com/cityjson/cjio/develop/README.rst).
- `py3dtiles`, which is a Python library for working with **3D Tiles**,
  especially point clouds, but again it is a low-level format library rather
  than an NYC-specific data-prep toolkit
  [py3dtiles README](https://raw.githubusercontent.com/Oslandia/py3dtiles/master/README.rst).
- `CityTiler`, which converts CityGML to 3D Tiles, but its own README says it
  focuses on **untextured LoD2 buildings** and requires a heavier stack
  including **3DCityDB, PostgreSQL, and PostGIS**; that is much more
  infrastructure-heavy than your “shallow dependency, pip-installable, web-ready
  outputs” positioning
  [CityTiler README](https://raw.githubusercontent.com/Jeremy-Gaillard/CityTiler/master/README.md).

So the gap is **not** “nobody can parse CityGML.” The gap is: there does not
appear to be a well-known package that is simultaneously **NYC-specific,
Python-first, lightweight, and optimized for web-consumable outputs from NYC’s
raw CityGML/LiDAR sources**
[cjio README](https://raw.githubusercontent.com/cityjson/cjio/develop/README.rst)
[CityTiler README](https://raw.githubusercontent.com/Jeremy-Gaillard/CityTiler/master/README.md)
[Web search: NYC CityGML LiDAR tools](https://github.com/Jeremy-Gaillard/CityTiler).

The right differentiation line for `nyc-mesh` is:

- not “another 3D GIS library”
- but “the easiest way to go from NYC open 3D source files to browser-friendly
  neighborhood meshes and analysis-ready exports”
  [cjio README](https://raw.githubusercontent.com/cityjson/cjio/develop/README.rst)
  [py3dtiles README](https://raw.githubusercontent.com/Oslandia/py3dtiles/master/README.rst)

## `subway-access`

This is also a real gap, but it is the **most likely to overlap with prior
civic-tech work**, so you need to position it carefully. There are existing
repos and datasets around MTA accessibility, but I did not find a clearly
dominant, actively maintained library that packages the full “ADA status +
outage reliability + catchments + equity scoring” workflow as a reusable product
[tsdataclinic/mta README](https://raw.githubusercontent.com/tsdataclinic/mta/master/README.md)
[MTA elevator/accessibility developer docs](https://mta.info/developers/display-elevators-NYCT)
[Web search: MTA accessibility analysis tools](https://github.com/TangoYankee/subway-ada-sdss).

The closest incumbent is `tsdataclinic/mta`. It is strong and relevant, but the
README explicitly says the project is **no longer maintained by Two Sigma**, and
what it ships are mainly **data products, graph pipelines, turnstile processing,
and crosswalks**, not a polished, public package with a simple analyst-facing
API and reproducible scoring workflow
[tsdataclinic/mta README](https://raw.githubusercontent.com/tsdataclinic/mta/master/README.md).
That is actually good news for you: it means there is prior art, but not a
locked-up winner
[tsdataclinic/mta README](https://raw.githubusercontent.com/tsdataclinic/mta/master/README.md).

Other adjacent projects exist, but they are narrower:

- `MTA-GTFS-ADA-Subway-Stations` is basically an augmented GTFS `stops.txt` with
  ADA columns, not a full analyzer
  [MTA-GTFS-ADA-Subway-Stations README](https://raw.githubusercontent.com/newyorkhack/MTA-GTFS-ADA-Subway-Stations/master/README.md).
- `nyc-subway-time` is a CLI for arrivals, service info, and ADA access, not a
  planning/equity analysis toolkit
  [nyc-subway-time README](https://raw.githubusercontent.com/otherfutures/nyc-subway-time/main/README.md).
- The MTA itself provides the raw ingredients: canonical station accessibility
  data plus live equipment and outage feeds, but not the kind of composite
  reliability/equity analysis you’re proposing
  [MTA elevator/accessibility developer docs](https://mta.info/developers/display-elevators-NYCT).

So the gap here is **not** “nobody has touched subway accessibility.” The gap
is: there is no obvious popular OSS library that turns those official feeds plus
street-network analysis plus demographics into a **repeatable accessibility
scoring and gap-analysis toolkit**
[tsdataclinic/mta README](https://raw.githubusercontent.com/tsdataclinic/mta/master/README.md)
[MTA elevator/accessibility developer docs](https://mta.info/developers/display-elevators-NYCT).

The right differentiation line for `subway-access` is:

- not “we have ADA station data”
- but “we measure how accessible the system is in practice, over time, for
  actual neighborhoods”
  [MTA elevator/accessibility developer docs](https://mta.info/developers/display-elevators-NYCT)
  [tsdataclinic/mta README](https://raw.githubusercontent.com/tsdataclinic/mta/master/README.md)

## `nyc311`

This also looks like a genuine gap, and the evidence is pretty consistent: there
are lots of **analysis notebooks** and some **LLM-ish demos**, but I did not
find a popular reusable package that packages NYC 311 topic extraction, anomaly
detection, and resolution-gap analysis into a stable library/CLI
[smart-311 README](https://raw.githubusercontent.com/hersh-gupta/smart-311/main/README.md)
[nyc-311-analytics README](https://raw.githubusercontent.com/rajatrayaraddi/nyc-311-analytics/main/README.md)
[PyPI search: Socrata + 311 packages](https://pypi.org/project/sodapy/).

The strongest “not actually your competitor” result is `smart-311`. It is about
improving **municipal 311 request processing at intake time** using multimodal
models, which is a different problem from mining the historical NYC 311 corpus
for topics, trends, and neighborhood anomalies
[smart-311 README](https://raw.githubusercontent.com/hersh-gupta/smart-311/main/README.md).

The closest adjacent analysis repo is `nyc-311-analytics`, which is interesting
and recent, but it is framed as a **notebook-based analysis project** with
`main.ipynb`, anomaly notebooks, data reduction notebooks, and a draft paper,
not a reusable package with a clean API/CLI and documented reproducible outputs
[nyc-311-analytics README](https://raw.githubusercontent.com/rajatrayaraddi/nyc-311-analytics/main/README.md).

On the package side, I found tools for **getting Socrata data** such as `sodapy`
and `socrata-py`, but the search did **not** surface a PyPI package with
built-in NYC 311 topic modeling or anomaly detection
[PyPI search: Socrata + 311 packages](https://pypi.org/project/sodapy/). That
suggests the ecosystem has ingestion clients and one-off studies, but not your
proposed product
[PyPI search: Socrata + 311 packages](https://pypi.org/project/sodapy/).

So the gap here is **not** “nobody analyzes 311.” The gap is: there does not
seem to be a recognized OSS package that lets someone say “give me
borough-filtered 311 data, cluster fine-grained complaint topics, detect topic
spikes by geography, and export a report”
[nyc-311-analytics README](https://raw.githubusercontent.com/rajatrayaraddi/nyc-311-analytics/main/README.md)
[smart-311 README](https://raw.githubusercontent.com/hersh-gupta/smart-311/main/README.md).

The right differentiation line for `nyc311` is:

- not “another NYC 311 notebook”
- but “a reproducible complaint-intelligence toolkit with CLI + package +
  reportable outputs”
  [nyc-311-analytics README](https://raw.githubusercontent.com/rajatrayaraddi/nyc-311-analytics/main/README.md)

## Bottom Line

My read is:

- `nyc-mesh`: **strongest greenfield gap**
  [cjio README](https://raw.githubusercontent.com/cityjson/cjio/develop/README.rst)
  [CityTiler README](https://raw.githubusercontent.com/Jeremy-Gaillard/CityTiler/master/README.md)
- `nyc311`: **also a strong gap**, especially if you package it like a real
  library instead of a notebook dump
  [smart-311 README](https://raw.githubusercontent.com/hersh-gupta/smart-311/main/README.md)
  [nyc-311-analytics README](https://raw.githubusercontent.com/rajatrayaraddi/nyc-311-analytics/main/README.md)
- `subway-access`: **real but more adjacent-to-existing-civic-work**, so you
  should emphasize reliability scoring, equity framing, and a cleaner reusable
  API than prior repos offered
  [tsdataclinic/mta README](https://raw.githubusercontent.com/tsdataclinic/mta/master/README.md)
  [MTA elevator/accessibility developer docs](https://mta.info/developers/display-elevators-NYCT)

If you want the safest anti-duplication positioning, I’d frame them like this:

- `nyc-mesh`: “NYC open 3D geodata to web-ready meshes and analysis exports”
- `subway-access`: “reliability-aware accessibility analysis, not just ADA
  labels”
- `nyc311`: “complaint intelligence package, not a one-off notebook”

That is different enough from the existing landscape that I would not worry
you’re just rebuilding a famous incumbent repo
[cjio README](https://raw.githubusercontent.com/cityjson/cjio/develop/README.rst)
[tsdataclinic/mta README](https://raw.githubusercontent.com/tsdataclinic/mta/master/README.md)
[nyc-311-analytics README](https://raw.githubusercontent.com/rajatrayaraddi/nyc-311-analytics/main/README.md).

If you want, I can next do the more tactical version of this: for each of the
three, I can give you a **“what to ship in v0.1 so it is clearly not
redundant”** checklist.

## Sources

- [cjio README](https://raw.githubusercontent.com/cityjson/cjio/develop/README.rst)
  (Mar 2026)
- [CityTiler README](https://raw.githubusercontent.com/Jeremy-Gaillard/CityTiler/master/README.md)
  (Mar 2026)
- [py3dtiles README](https://raw.githubusercontent.com/Oslandia/py3dtiles/master/README.rst)
  (Mar 2026)
- [Web search: NYC CityGML LiDAR tools](https://github.com/Jeremy-Gaillard/CityTiler)
  (Mar 2026)
- [Web search: PyPI CityGML / 3D Tiles packages](https://pypi.org/project/cjio/)
  (Mar 2026)
- [tsdataclinic/mta README](https://raw.githubusercontent.com/tsdataclinic/mta/master/README.md)
  (Mar 2026)
- [MTA elevator/accessibility developer docs](https://mta.info/developers/display-elevators-NYCT)
  (Mar 2026)
- [MTA-GTFS-ADA-Subway-Stations README](https://raw.githubusercontent.com/newyorkhack/MTA-GTFS-ADA-Subway-Stations/master/README.md)
  (Mar 2026)
- [nyc-subway-time README](https://raw.githubusercontent.com/otherfutures/nyc-subway-time/main/README.md)
  (Mar 2026)
- [Web search: MTA accessibility analysis tools](https://github.com/TangoYankee/subway-ada-sdss)
  (Mar 2026)
- [smart-311 README](https://raw.githubusercontent.com/hersh-gupta/smart-311/main/README.md)
  (Mar 2026)
- [nyc-311-analytics README](https://raw.githubusercontent.com/rajatrayaraddi/nyc-311-analytics/main/README.md)
  (Mar 2026)
- [PyPI search: Socrata + 311 packages](https://pypi.org/project/sodapy/)
  (Mar 2026)
