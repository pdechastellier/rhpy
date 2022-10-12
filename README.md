
# RHPY

Modern API on legacy RHPI tool that manage vacations and leaves

## Not supported
* multiple contract. It only takes the first one

# Mac Installation

1. Download Chrome
2. Download Chromedriver, with same version number as Chrome
https://chromedriver.chromium.org/downloads
3. Move the driver to the /usr/local/bin folder



# Docker
## Build
```
docker build -t pdechastellier/rhpy:0.9 .
```
## Run and attach
```
docker run --rm -ti pdechastellier/rhpy:0.9 /bin/bash
```

Vulnerability scan - snyk
docker scan