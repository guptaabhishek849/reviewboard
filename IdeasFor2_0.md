# Introduction #

This is a dumping ground for ideas we'd like to see in Review Board 2.0. Some features are definitely planned while some are just possibilities.


## Hooks and Extensions ##

One of the big features of 2.0 will be support for hooks and extensions. Hooks are simple scripts that are invoked under certain operations (posting a new review request, or a new review). Extensions are pluggable components that users can install that will provide additional functionality to the product. These might provide new UI (for example, additional fields in the review request details box, a new section of the UI for custom data, or even a whole new front-end).

The plan is to turn the current iPhone UI into an extension. We might even make the Reports view an extension as well.

We may decide not to implement a separate concept for hooks and instead just use extensions, so that they can be managed easier. If done correctly, extensions will be really simple to write.

Feature requests tagged with [Extensions](http://code.google.com/p/reviewboard/issues/list?q=milestone%3AExtensions) are candidates for future extensions.


## New Reviewable File Types ##

There has been some request for reviewing files other than diffs. Screenshots have been the main one, though someone suggested Wiki changes and specialized views for certain text documents.

It would be nice to make our current comment setup a bit more generalized and allow new models provided by extensions to associate a comment with their own data. These comments would be part of the review, and would have the extension render the necessary comments in the review. The extension would also be responsible for providing the whole review UI for this file type.

This would need some help from post-review, as binary files are not included in diffs. We would have to manually upload some files. Perhaps we can expose a list of supported mimetypes and file extensions for review, accessible through the API, and have post-review query that when deciding what to include in the diff.


## CIA Support ##

[CIA](http://www.cia.vc/) is a tool developed to keep track of commits to code repositories. These commits are often relayed to project IRC channels. Some projects use it for their issue trackers. We could use it to notify when there are new review requests or reviews, giving people in project channels instant notification and a URL. This would be an extension and not built into the codebase.


## Attach Arbitrary Links ##

Likewise, it may be useful to have a list of links associated with a review request (such as a specialized diff for users that haven't seen the light yet). This would be fairly easy to add if we decided to do it.