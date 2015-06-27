# Introduction #

Here are listed basic concepts of the upcoming python interface for RB API v2.

## Basic idea ##

RBTools is a neat tool for those valuing time and efficentcy. Unfortunately, with time it became an oversized solid script which is tedious to maintain.

The key to the new API interface is the Review Board resources. All they have regular structure and we can put this advantage to use in our python interface. Let us take a closer look on these resources. Each resource is a JSON object and has two kinds of properties: scalar and compound.

Let us look how it will work. Consider the simplest example where you are need to connect to a Review Board server and fetch its properties. The corresponding information can be retrieved using `GET` request to the [Server Info Resource](http://www.reviewboard.org/docs/manual/dev/webapi/2.0/resources/server-info/).

```python

from rbtools.api.client import RBClient

def main():
root = RBClient('http://example.com').get_root()
info = root.get_info()
print info.name, ' ', info.version
```

The following output should be printed:

```
Review Board 1.7 alpha 0 (dev)
```

That is pretty simple, is not it? All you need is just open the Review Board docs page and search for the required resource in order to know that methods and properties it has.

But what is about direct requests? With the current approach it is possible to fetch a resource directly in single HTTP request. Foretunately, the Root Resource has a number of template URIs for accesing all kind of resources directly.

# Components #

## Modules ##

### rbtools.api ###

### rbtools.clients ###

### rbtools.commands ###

### rbtools.utils ###

## Command-line interface ##

# Future plans #

**TODO**

# Relevant links #

  1. [Review Board REST API 2.0](http://www.reviewboard.org/docs/manual/dev/webapi/#rest-api-2-0)
  1. [The interface design discussion](https://groups.google.com/d/topic/reviewboard-dev/HFm7rz4QE2k/discussion)
  1. [New commands layout discussion](https://groups.google.com/d/topic/reviewboard-dev/MLOFW3DqoaM/discussion)