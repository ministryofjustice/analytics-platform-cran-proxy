# Analytics Platform Cran Proxy

[![Docker Repository on Quay](https://quay.io/repository/mojanalytics/cran-proxy/status "Docker Repository on Quay")](https://quay.io/repository/mojanalytics/cran-proxy)

- [Description](#description)
- [Background](#background)
- [Security](#security)
- [Usage](#usage)
- [API](#api)
- [License](#license)

# Description

A cran mirror that compiles binary packages for the rocker:verse environment.

## Why

CRAN servers usually provide binary versions of libraries for Windows and OSX
but not for Linux. This is understandable because there's no such thing as
*"Linux OS"*. Each distribution will have a set of C libraries, version of
`libc` or a different implementation of `libc` altogether (`musl`). If you
wanted to support linux you'd have to compile hundreds of versions of each
R package to cope with a myriad of linux options. Even if you did this,
there would be a discovery problem because there is no good way for your
flavor of linux to find an R package compiled for it.

However, in our environment we've standardised on using the `rocker:verse`
docker images images with a pinned version of R (3.4). Given we know the
constraints it is possible to run a CRAN server that provides pre-compiled
R package binaries for `rocker:verse`. 🆒

This is where the R ecosystem gets in the way. When you do
`install.packages('pkg', type = 'binary')` R is able to convert that to
`win.binary` or `osx.binary` depending on your operating system and R version
then look in the right place on the CRAN server for the right package. This
doesn't happen on Linux. Instead of trying to hack the R `install.packages`
function this proxy does something **non-standard**. It will, if it has a
compiled copy of a source package, send that version **instead** of the source
package requested.

R's `install.packages()` and `Packrat` both handle this and don't rebuild the
binary even if they were expecting a source package. This is crucial in making
this work.

## Gotchas

-   If you were to use this cran-proxy in a Windows or Mac environment you might
    get sent Linux binary packages. I don't know what R will do when this
    happens
-   The proxy is unaware of R version. It will send you binaries for the R
    version it is running. This means we'll need 1 instance of the cran-proxy
    for every version of R we want to support. R packages are generally
    compatible across patch version so cran-proxy running R 3.4.3 will be fine
    for clients using R 3.4.2
-   If your Linux environment is subtly different from what the cran-proxy is
    running on, your packages might install successfully but crash at run-time

# Background

This was created to solve a [real
issue](https://github.com/ministryofjustice/analytics-platform/issues/3) for our
users who experience slow Packrat installs. Our users run the web based version
of R-Studio so their OS is Linux, but official CRANs don't provide Linux
binaries.

# Security

The proxy doesn't have any endpoints that allow you to upload anything. It will
only proxy GET requests upstream so from a web perspective it's relatively hard
to exploit. 

The main area of concern is that the compilation happens inside the
same container that is running the cran-proxy. 
Ideally this would happen in a
fresh container where we copy the compiled binary out of.

# Usage

## End users

### install.packages

If you just want to try it then you can do:

```R
install.packages('package', repos='https://cran-proxy.yourserver.com')
```

If you want to persist this then add

```R
options(repos = c(CRAN = 'https://cran-proxy.services.dev.mojanalytics.xyz'), download.file.method = 'libcurl')
```

to your `.Rprofile` file.

### Packrat

Update your `packrat.lock` file to point at the proxy from:

```R
PackratFormat: 1.4
PackratVersion: 0.4.8.1
RVersion: 3.4.0
Repos: CRAN=https://cloud.r-project.org/
```

to:

```R
PackratFormat: 1.4
PackratVersion: 0.4.8.1
RVersion: 3.4.0
Repos: CRAN=https://cran-proxy.yourdomain.com
```

## Administrators

### Environment Variables

| Name | Default | Description |
|------------------------- |------------------------------ |-------------------------------------------------------------------------------------------------------- |
| `DEBUG` | `FALSE` | If set to true the webserver will auto reload on changes, dump exceptions and set the log level to DEBUG |
| `PASSIVE` | `FALSE` | If set to TRUE, the server will not attempt to compile any packages and will always return source packages |
| `PORT` | `8000` | TCP Port to listen for HTTP requests on |
| `UPSTREAM_CRAN_SERVER_URL` | `https://cloud.r-project.org/` | URL of CRAN server we are proxying. <span class="underline">Include trailing slash</span> |
| `LOG_LEVEL` | `INFO` | Can be one of `INFO`, `WARNING`, `ERROR`, `DEBUG` |
| `BINARY_OUTPUT_PATH` | `/tmp/bin/` | Place to store built binaries. If it doesn't exist it'll be created on server start. |

### Deployment

This proxy can be deployed to a Kubernetes cluster using Helm using the
corresponding
[chart](https://github.com/ministryofjustice/analytics-platform-helm-charts/tree/master/charts/cran-proxy).

# API

-   If the request is to `/src/contrib/PACKAGES` in which case it proxies it
-   else if it is a request directly to a package's `.tar.gz` in which case it
    checks the local cache of built packages and serves the binary if it exists or
    sends a 302 to the upstream and adds it to a compile queue so future requests
    will get a precompiled binary.
-   else the proxy returns a HTTP 302 to the same path on the upstream server 

## Additional Endpoints

### `/metrics`

Prometheus metrics endpoint

### `/healthz`

Always returns a HTTP 200 OK (with no-cache headers)

## Contributing

PRs welcome but please ensure tests pass before sending a PR because we don't
have CI setup yet.

There is long [list](../issues?q=label%253Aenhancement) of possible improvements
in the issue tracker tagged with **enhancement**.

# License

[MIT © Ministry of Justice](../LICENSE)
