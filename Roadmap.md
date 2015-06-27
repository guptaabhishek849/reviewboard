# Review Board 1.5 Roadmap #

This describes the roadmap for the 1.5 release of Review Board, including an estimated schedule, features we expect to have in the release, and bugs we want to fix.


## Schedule ##

Review Board 1.0 was released on June 20, 2009. Since then, we've had a lot of development, including the Google Summer of Code. We hope to have a 1.5 release by March 2010. This may change due to many factors, but we're proceeding with this goal in mind.

The release process will be:

  * **Alpha 1:** Most of our [must-have features](#Must_Have_Features.md) should be implemented.
    * **Release Date:** Saturday, September 19th, 2009
  * **Alpha 2:** All of our [must-have features](#Must_Have_Features.md) must be implemented. Many of our [Milestone-1.1 bugs](#Bugs.md) will still be open, but no new features will be added outside what's on this roadmap without a compelling case. We hope to have most of our contributed patches that are ready to commit in this release. Non-trivial contributions will be pushed to our next release.
    * **Release Date:** Monday, October 11, 2009
  * **Beta 1:** All ["maybe" features](#Maybe_Features.md) that we decide we want in 1.5 must be implemented. All other features will be pushed back to the next release. The focus after this will be on documentation and bug fixes.
    * **Release Date:** Saturday, January 16, 2010
  * **Beta 2:** All medium and high priority [Milestone-1.5 bugs](#Bugs.md) should be fixed.
    * **Release Date:** Monday, February 6, 2009
  * **Release Candidate 1:** Additional [Milestone-1.5 bugs](#Bugs.md) fixed as necessary.
    * **Release Date:** Saturday, March 6, 2010
  * **Final Release**
    * **Scheduled Release:** Saturday, March 20, 2010


## Release Dependencies ##

  * **Django 1.1:** Review Board's biggest dependency is [Django](http://www.djangoproject.com/). Django 1.1 released on July 29, 2009.
  * **Django Evolution:** [Django Evolution](http://django-evolution.googlecode.com/) is another important dependency. Their release schedule is unknown but we'll likely depend on either a snapshot of their Subversion repository or the closest stable release at the point of our release.


## Release 1.5 (formerly 1.1) ##

### Must-Have Features ###

| **Feature**                                | **Status**                     |
|:-------------------------------------------|:-------------------------------|
| Dynamic update notifications               | Committed (ce1eeed)            |
| Hosting service easy-config                | Committed (52c49a8)            |
| Screenshot drag-and-drop upload            | Committed (621f6ac)            |
| HTML email support                         | Committed (05a8aeb)            |
| Raw-file URL remote Git support            | Committed (8df8d29)            |
| Toggling whitespace display in diff        | Committed (629bbc1)            |
| Move detection                             | Committed (c52c1bf)            |
| Repository validation                      | Committed (fccd8bd)            |
| SSH and HTTPS support                      | Committed (fccd8bd)            |


### Maybe Features ###

| **Feature**                       | **Issue Number**  | **Status**            |
|:----------------------------------|:------------------|:----------------------|
| Real names in drop-downs          | [issue 598](https://code.google.com/p/reviewboard/issues/detail?id=598)       | Committed (245ab23)   |
| Function headers in diff viewer   | [issue 114](https://code.google.com/p/reviewboard/issues/detail?id=114)       | Committed (7ef6e62)   |


### Bugs ###

We have a list of bugs we'd like to fix for 1.5. Any and all bugs that we can fix should be fixed, but we specifically mark some as Milestone-Release1.5.

  * [Milestone-Release1.5 bug list](http://code.google.com/p/reviewboard/issues/list?can=2&q=milestone:Release1.5)


## Release 2.0 ##

### Must-Have Features ###

| **Feature**                      | **Issue Number**  | **Status**    |
|:---------------------------------|:------------------|:--------------|
| User/group access policies       |                   | Not started   |
| Third-party extensions           |                   | Not started   |

### Bugs ###

We have a list of bugs we'd like to fix for 2.0. Any and all bugs that we can fix should be fixed, but we specifically mark some as Milestone-Release2.0.

  * [Milestone-Release2.0 bug list](http://code.google.com/p/reviewboard/issues/list?can=2&q=milestone:Release2.0)