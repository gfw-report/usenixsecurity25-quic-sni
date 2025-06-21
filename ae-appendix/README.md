# USENIX Security 2025 AE Template

## Build

The repository is configured to build via GitHub Actions on each commit
and store the compiled paper as artifact in the GitHub Action. See
[.github/workflow/compile.yml](.github/workflow/compile.yml) for
details.

Alternatively, the repository can be built locally via act or make.

### Build with act

Run ```run_workflow.sh```. This requires Docker to work locally as well as
an installation of [act](https://github.com/nektos/act). This starts the
GitHub Action to compile the paper and copies the ```paper.pdf``` to this
directory. Due to artifacts not working with act it may show errors.

### Build with make

Run ```make```. This requires an installation of LaTeX and make locally on
your machine and compiles the TeX files into ```paper.pdf```.'

### Build with Docker

Export environment variable ```LATEX_BUILD_ENV=docker``` and run ```make```. This
requires a working Docker CLI (aka ```docker run <image>```) and produces
a ```paper.pdf```.

## usenixbadges.sty --- affix USENIX Artifact Evaluation badges

The `usenixbadges` LaTeX style file affixes USENIX Artifact Evaluation
badges to the front page of your USENIX-formatted paper (or standalone Appendix).

### Installation

Put `usenixbadges.sty` and the `usenixbadges-*.pdf` graphics files in
the directory that contains the LaTeX source for your paper.  (Really,
you can put them anywhere in LaTeX's search path, but the simplest
thing is to put the files in the same directory as your paper's LaTeX
source files.)

### Usage

In the preamble of your LaTeX document, insert a line like this:

```
  \usepackage[<options>]{usenixbadges}
```

In the options, list the badges that have been awarded to your paper.
The possible badges are:

  * `available`  --- affix the "Artifacts Available" badge
  * `functional` --- affix the "Artifacts Functional" badge
  * `reproduced` --- affix the "Results Reproduced" badge

Example:

```
  %% Affix the indicated badges to the paper.
  \usepackage[available,functional]{usenixbadges}
```

Tips:

* In your LaTeX document, the `\usepackage[...]{usenixbadges}` directive
must come after `\documentclass` and before `\begin{document}`.

* If your LaTeX document has many `\usepackage` directives, put
`\usepackage[...]{usenixbadges}` near the end of those.  This may
avoid problems relating to conflicting options for the `graphicx`
package.
