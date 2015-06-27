# Introduction #

This page lists some of the ideas we've come up with that students could tackle
for student projects. Proposals can be made based on items in this list, or you
can propose something entirely new.

You can also look at our bugs marked
[ExtensionIdea](http://code.google.com/p/reviewboard/issues/list?can=2&q=label:ExtensionIdea) for more ideas.


# Diff Viewer Projects #


## Inline File Attachments ##

Review Board 1.6 introduced support for file attachments. They were standalone
and tied to a review request. We should also allow them to be uploaded and tied
to a diff, for binary files that otherwise wouldn't be able to be displayed.

This would involve updating the FileAttachment model to contain a source
revision field, which, along with its filename, would match data in a FileDiff.
These file attachments should be filtered out from the main review request
display.

The diff viewer, upon encountering a binary file that can't be displayed, should
look up a matching FileAttachment and display an entry for that inline.

A good addition would be to have a clean mechanism for registering a class that
would know how to render a file attachment in the diff viewer. It would be keyed
off by a mimetype. This mechanism should also be extensible so that extensions can
register themselves to handle particular mimetypes. A built-in one could render images.
The fallback would be to display a UI similar to that of the file attachments on the review
request page.

The web API would need to be updated to know how to filter, to take params for
the source revision, and to be able to get a related FileAttachment from a
FileDiff.

Once completed, we should replace the current screenshot review UI with the image attachment
binary file handler.

post-review would need to be updated to optionally upload binary files (under a
certain size) using this API.

**Code coverage:**

  * `rbtools`
  * `reviewboard/attachments`
  * `reviewboard/reviews/views.py`
  * `reviewboard/templates/diffviewer`
  * `reviewboard/webapi/resources.py`


# Review Request Projects #


# Extension Projects #

## Pluggable Review UIs ##

We now have the ability to add new review UIs for different file types via
extensions. We'd like to add more handlers for different mimetypes. These
can range anywhere from plain text to diagrams to Microsoft Word or PDF
documents.

## Admin Widgets ##

The admin site has a bunch of "widgets" that show information and allow the
user to configure the site. We'd like extensions to be able to add them.

## Automated Static Analysis ##

Progress has been made to run static analysis tools automatically on code posted to
review board. The system currently runs the PEP8 style checker on python code, but additional
plugins must be written to support other tools.

Other possible projects include improvements to the tool plugin API, the admin UI, and
a system for tools to be triggered manually using the web UI.

**Create a new static analysis plugin for Review Bot**
  * Pick a static analysis tool (jslint, pylint, Buildbot "try",  etc.) and write the plugin
  * Difficulty: easy - moderate (depending on the complexity of the tool)
  * Code Coverage: Parsing, Review Bot's Tool API.

**Implement logging of tool execution**
  * Currently Review Bot fires off requests for the tool execution, but does not keep track of this. If a review isn't posted it's impossible to know if an attempt to execute a tool was made without checking the logs of every worker. Creating a record in the database of which tools were executed, and if they succeeded could be useful for administration.
  * Difficulty: moderate
  * Cover Coverage: Review Board extensions, Web API, Celery.

**Improve the Review Bot tool API**
  * Currently tools only posses a simple API for basic reviews of diffs. This could involve adding functionality for working with file attachments and screenshots, or other improvements
  * Difficulty: easy - moderate
  * Code Coverage: Review Bot's Tool API, Web API, Review Board extensions.

**Improve Review Bot's Configuration options**
  * The global review bot configuration options were quickly thought up. It might be worth rethinking them, figuring out what would be best to have. It would also be nice to figure out a way to make it easy for tools to obey the settings.
  * Difficulty: easy - moderate
  * Code Coverage: Review Board extensions, Review Bot's admin UI and Tool API.

## Checklist Extension ##

Oftentimes, a development team will have a checklist of items that they need to be looking for in their code reviews (for example, "Make sure all variable names are camel-cased"). Or, if a reviewer notices that a certain type of defect keeps slipping through their reviews, they might want to add it to their checklist in order to make sure they look for it next time.

A checklist extension would help here.

### General Requirements / Specifications ###

  * Allows teams and projects to have shared checklists
  * Allows individual users to add custom items to their lists
  * The list should be light-weight in operation, and minimal in appearance so as to keep focus on the code being reviewed.
  * Remember checked items per review (if I save a review draft, and log-in from another computer to continue, my checklist should remember what items I've already checked off)
  * Remind the user if they try to publish a review with unchecked items on their list, in case they want to keep reviewing.


# Web API Projects #

## Polish and Land Python Web Client Tools ##

There's been an ongoing effort to replace the useful, yet convoluted post-review
tool with a set of smaller tools and scripts that operate with the Review Board
Web API.

We need to polish up the work that's been done so far, as well as write new scripts
for new functionality.

# Hosting Service Projects #

## Repository Auto-Configuration ##

We should update the repository management tool to support auto-configuration from a hosting service.

For example, the user should be able to register their GitHub account as a hosting service, and then the
management tool should list all of the repositories available to that account. The user should then be able
to just check off the repositories that they'd like to add.

There are workflow issues to solve here though, so this requires some investigation and research.

## Better Bug Tracker Integration ##

We'd like to allow the user to configure a bug tracker that could be associated with their repositories,
and to extend our HostingService support to allow posting to the bug trackers via their APIs.

# General Web UI Projects #

## Fewer Reloads ##

Many operations today reload the page. For example, publishing a draft of a
review, or discarding, or closing a review request.

Ideally, we would be able to make some of these changes more dynamic. Instead of
doing a full reload, it would just dynamically update the page content.

The one trick with this work is making sure we don't have too many redundant
bits of UI. If we're rendering some stuff on initial page load from the
templates and then rendering separately on demand via JavaScript, we could get
into some inconsistencies down the road. So this would need a solution.

An option would be to have URLs that render the page content instead. Change
history descriptions, for example. Then it's handled in one place.

Some simple tasks here would be to handle the case of review drafts, so that
they don't reload the page. There, we're talking simple CSS class changes, or
removing elements.

This is a bit of a general task, and we'd need to figure out the specifics.

**Code coverage:**

  * `reviewboard/htdocs/media/rb/js`
  * `reviewboard/reviews`
  * `reviewboard/templates`

## Admin Site Configurability ##

Right now, the admin site has a bunch of widgets, but they're always all visible
and in a hard-coded order. We'd like admins to be able to add and remove
widgets and drag them around to customize their view.

**Code coverage:**

  * `reviewboard/admin`
  * `reviewboard/templates`