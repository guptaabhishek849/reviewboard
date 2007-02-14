// Constants
var BACKWARD = -1;
var FORWARD  = 1;
var INVALID  = -1;
var DIFF_SCROLLDOWN_AMOUNT = 100;
var VISIBLE_CONTEXT_SIZE = 5;

var gActions = [
	{ // Previous file
		keys: "aAKP<m",
		onPress: function() { scrollToAnchor(GetNextFileAnchor(BACKWARD)); }
	},

	{ // Next file
		keys: "fFJN>/",
		onPress: function() { scrollToAnchor(GetNextFileAnchor(FORWARD)); }
	},

	{ // Previous diff
		keys: "sSkp,,",
		onPress: function() { scrollToAnchor(GetNextAnchor(BACKWARD)); }
	},

	{ // Next diff
		keys: "dDjn..",
		onPress: function() { scrollToAnchor(GetNextAnchor(FORWARD)); }
	},

	{ // Recenter
		keys: unescape("%0D"),
		onPress: function() { scrollToAnchor(gSelectedAnchor); }
	},

	{ // Go to header
		keys: "gu;",
		onPress: function() {}
	},

	{ // Go to footer
		keys: "GU:",
		onPress: function() {}
	},
];

// State variables
var gSelectedAnchor = INVALID;
var gCurrentAnchor = 0;

Event.observe(window, 'load', onPageLoaded, false);

function keyCode(evt) {
	if (navigator.appName.indexOf("Explorer") != -1) {
		return evt.keyCode;
	} else {
		return evt.which;
	}
}

function onKeyPress(evt) {
	var keyChar = String.fromCharCode(keyCode(evt));

	for (var i = 0; i < gActions.length; i++) {
		if (gActions[i].keys.indexOf(keyChar) != -1) {
			gActions[i].onPress();
			return;
		}
	}
}

function gotoAnchor(name) {
	return scrollToAnchor(GetAnchorByName(name));
}

function GetAnchorByName(name) {
	for (var anchor = 0; anchor < document.anchors.length; anchor++) {
		if (document.anchors[anchor].name == name) {
			return anchor;
		}
	}

	return INVALID;
}

function onPageLoaded(evt) {
	/* Skip over the change index to the first item */
	gSelectedAnchor = 1;
	SetHighlighted(gSelectedAnchor, true)

	Event.observe(window, 'keypress', onKeyPress, false);
}

function addComments(fileid, lines) {
	var table = $(fileid);

	for (line in lines) {
		var row = table.rows[line];
		var cell;

		if (row.cells.length == 4) {
			cell = row.cells[1];
		} else {
			cell = row.cells[0];
		}

        cell.innerHTML = "<a name=\"line" + line + "\">" + line + "</a>";

		// TODO: Count the number of comments
		var commentNode = Builder.node('span',
			{class: 'commentflag',
			 style: 'top: ' + GetYPos(cell) + 'px;'},
			lines[line]);
		cell.insertBefore(commentNode, cell.firstChild);
	}
}

function scrollToAnchor(anchor) {
	if (anchor == INVALID) {
		return false;
	}

	window.scrollTo(0,
		GetYPos(document.anchors[anchor]) - DIFF_SCROLLDOWN_AMOUNT);
	SetHighlighted(gSelectedAnchor, false);
	SetHighlighted(anchor, true);
	gSelectedAnchor = anchor;

	return true;
}

function GetYPos(obj) {
	return obj.offsetTop + (obj.offsetParent ? GetYPos(obj.offsetParent) : 0);
}

function GetNextAnchor(dir) {
	var newAnchor = gSelectedAnchor + dir;
	if (newAnchor < 0 || newAnchor >= document.anchors.length) {
		return INVALID;
	}

	var name = document.anchors[newAnchor].name;

	if (name == "index_header" || name == "index_footer") {
		return INVALID;
	}

	return newAnchor;
}

function GetNextFileAnchor(dir) {
	var fileId = document.anchors[gSelectedAnchor].name.split(".")[0];
	var newAnchor = parseInt(fileId) + dir;
	return GetAnchorByName(newAnchor);
}

function SetHighlighted(anchor, highlighted) {
	var anchorNode = document.anchors[anchor];
	var node = anchorNode.parentNode;
	var nextNode = anchorNode.nextSibling.nextSibling;
	var controlsNode;

	if (node.tagName == "TD" || node.tagName == "TH") {
		node = node.parentNode;
		controlsNode = node.getElementsByTagName('th')[0].firstChild.nextSibling;
	}
	else if (nextNode.className == "sidebyside") {
		node = nextNode.getElementsByTagName('tr')[0];
		controlsNode = node.getElementsByTagName('th')[0].firstChild;
	}
	else {
		return;
	}

	if (highlighted) {
		controlsNode.nodeValue = "▶";
	} else {
		controlsNode.nodeValue = "";
	}
}

function toggleChunkCollapse(tbody) {
	for (var i = VISIBLE_CONTEXT_SIZE;
	     i < tbody.rows.length - VISIBLE_CONTEXT_SIZE;
		 i++) {

		tbody.rows[i].toggle();
	}
}
