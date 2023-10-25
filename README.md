<div id="top"></div>

<!-- PROJECT SHIELDS -->
[![Github actions
status](https://github.com/rero/rero-ils/workflows/build/badge.svg)](https://github.com/rero/rero-ils/actions?query=workflow%3Abuild)
[![image](https://img.shields.io/coveralls/rero/rero-ils.svg)](https://coveralls.io/r/rero/rero-ils)
[![Release
Number](https://img.shields.io/github/tag/rero/rero-ils.svg)](https://github.com/rero/rero-ils/releases/latest)
[![License](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](http://www.gnu.org/licenses/agpl-3.0.html)
[![Gitter
room](https://img.shields.io/gitter/room/rero/reroils.svg)](https://gitter.im/rero/reroils)
[![Translation
status](https://hosted.weblate.org/widgets/rero_plus/-/rero-ils/svg-badge.svg)](https://hosted.weblate.org/engage/rero_plus/?utm_source=widget)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/rero/rero-ils">
    <img src=".github/images/logo-global.svg" alt="RERO ILS" width="80" height="80">
  </a>

<h2 align="center">RERO ILS</h2>

  <p align="center">
    The elegant solution for heritage, public and school libraries or networks.
    <br />
    <a href="https://ils.test.rero.ch/"><strong>Live Demo »</strong></a>
    ·
    <a href="https://ils.test.rero.ch/help/home"><strong>User docs »</strong></a>
    ·
    <a href="https://github.com/rero/developer-resources"><strong>Developer docs »</strong></a>
    <br />
    <br />
    <a href="https://www.rero.ch/produits/ils">Website</a>
    ·
    <a href="https://github.com/rero/rero-ils/issues">Report Bug</a>
    ·
    <a href="https://github.com/rero/rero-ils/issues">Request Feature</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#rero-ils">RERO ILS</a></li>
        <li><a href="#built-with">Built with</a></li>
      </ul>
    </li>
    <li>
      <a href="#usage">Usage</a>
      <ul>
        <li><a href="#demo">Demo</a></li>
        <li><a href="#features">Features</a></li>
        <li><a href="#use-rero-ils">Use RERO ILS</a></li>
      </ul>
    </li>
    <li><a href="#getting-started">Getting started</a></li>
      <ul>
        <li><a href="#install">Install</a></li>
        <li><a href="#the-ecosystem">The ecosystem</a></li>
      </ul>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>
<br />

# About the project

<div align="center">
  <a href="https://ils.test.rero.ch/">
    <img src=".github/images/screenshot.png" alt="RERO ILS" style="width:720px">
  </a>
</div>
<br />

## RERO ILS

RERO ILS is a new generation open source [integrated library system](https://en.wikipedia.org/wiki/Integrated_library_system) developed in Switzerland by [RERO+](https://rero.ch/) in collaboration with the Catholic University of Louvain ([UCLouvain](https://uclouvain.be/)). It allows the management of library networks or independent libraries (document acquisition, circulation, cataloguing, search) and offers a public interface for users.

RERO ILS has been under heavy development since 2017 as a replacement for RERO network's legacy software. Its first major release (`v1.0.0`) was published at the end of 2020. The first real-life production instance has been live since June 2021. Since then, it is being actively maintained and developed by a committed team from Switzerland and Belgium, in order to improve upon its current features and satisfy its users' needs.

## Built with

* [Invenio](https://github.com/inveniosoftware/invenio)
* [Flask](https://github.com/pallets/flask)
* [Angular](https://github.com/angular/angular)
* [ElasticSearch](https://github.com/elastic/elasticsearch)
* [Ngx-Formly](https://github.com/ngx-formly/ngx-formly)

<p align="right">(<a href="#top">back to top</a>)</p>

# Usage

## Demo

To explore the system, you can try the [test instance](https://ils.test.rero.ch/) or take a look at one of the production instances: [RERO+ network](https://bib.rero.ch/) (live since Summer 2021) and [UCLouvain network](https://ils.bib.uclouvain.be/) (live since early 2022).

## Features

* :globe_with_meridians: **Consortial model:** built primarily for library networks, large or small, with several levels of configuration included (organization, library).
* :books: **Cataloguing and serial management:** modern cataloguing editor in compliance with current standards (RDA, BibFrame); in-depth management of periodicals, subscriptions, and issue predictions.
* :computer: **Online catalog:** public online catalog with simple but powerful search and filtering functions; customizable views by organization and library; seamless integration of resources from external platforms (ebooks, databases, etc.).
* :book: **Circulation module:** perform all the operations required by libraries: check-out, check-in, item requests, interlibrary loans, patron management, in a modern, fast and ergonomic web interface.
* :arrows_clockwise: **Data interaction and openness:** JSON formatted bibliographic data [Bibframe model](https://www.loc.gov/bibframe/) with a powerful API to interact with the database.

## Use RERO ILS

RERO ILS is open source and can be can be deployed and hosted by anyone, provided they can afford the required configuration or development effort. It can also be hosted [*as a service*](https://www.rero.ch/en/products/ils#discover) by RERO+ for any interested library or organisation.

The [user documentation](https://ils.test.rero.ch/help/home/) for RERO ILS is hosted on [flask-wiki](https://github.com/rero/flask-wiki/).

<p align="right">(<a href="#top">back to top</a>)</p>

# Getting started

## Install

* The installation process is described in a [specific file](INSTALL.rst).
* To run a development environment you can check this [documentation](https://github.com/rero/developer-resources/blob/master/rero-instances/rero-ils/dev_installation.md).

## The ecosystem

### Three GitHub repositories for RERO ILS

The [rero-ils GitHub project](https://github.com/rero/rero-ils) contains the main project for RERO ILS, basically providing the `invenio` backend. To work on the frontend of the project, you also need [rero-ils-ui](https://github.com/rero/rero-ils-ui), which is based on [ng-core](https://github.com/rero/ng-core).

### MEF

The [MEF](https://github.com/rero/rero-mef) (*Multilingual Entity File*), provides authorities (or entities) to RERO ILS, in two languages: French and German (for now). This is used to link documents to controlled descriptions of authors and subjects. MEF can aggregate multiple authority files, such as [IdRef](https://www.idref.fr/) and [GND](https://www.dnb.de/DE/Professionell/Standardisierung/GND/gnd_node.html). These authority files are then aligned through [VIAF](https://viaf.org), thus providing multilingual authorities.

As a result, in order to run RERO ILS, you need to either use our [public MEF server](https://mef.test.rero.ch), or run your own.

### RERO EBOOKS

RERO ILS customers make use of 3rd-party ebook commercial platforms. A
dedicated server has been set up for harvesting ebook metadata from
those platforms, convert them to RERO ILS's own data model. RERO ILS
harvests our ebooks server, importing the metadata into the union
catalog, assigning each ebook to the corresponding subscribing
libraries.

This server is not publicly accessible but the source code is available on
GitHub: [rero-ebooks](https://github.com/rero/rero-ebooks).

You need to prevent your RERO ILS instance to harvest RERO's ebooks
server, but you can run your own ebooks server.

<p align="right">(<a href="#top">back to top</a>)</p>

# Contributing

Any contribution is **greatly appreciated**!

* To contribute to the code itself, please check the [contributing recommandations](https://github.com/rero/rero-ils/blob/dev/CONTRIBUTING.rst).
* The [developer-resources Github project](https://github.com/rero/developer-resources/) provides all kinds of references related to Invenio applications, more specifically RERO ILS.
* Found a bug or want to suggest a feature or an enhancement? [Open an issue](https://github.com/rero/rero-ils/issues/new).
* Want to help with the translation of the project? Visit our [Weblate project](https://hosted.weblate.org/projects/rero_plus/#information).

<p align="right">(<a href="#top">back to top</a>)</p>

# License

Distributed under the GNU Affero General Public License. See [`LICENSE`](LICENSE) for more information.

<p align="right">(<a href="#top">back to top</a>)</p>

# Contact

* If you have questions, you can ask the development team on [Gitter](https://gitter.im/rero/reroils).
* In case of a security issue, please contact the e-mail address provided in the [security policy](https://github.com/rero/rero-ils/blob/dev/SECURITY.rst).

<p align="right">(<a href="#top">back to top</a>)</p>
