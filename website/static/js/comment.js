/**
 * Controller for the Add Contributor modal.
 */
'use strict';

var $ = require('jquery');
var ko = require('knockout');
var moment = require('moment');
var Raven = require('raven-js');
require('knockout-mapping');
require('knockout.punches');
require('jquery-autosize');
ko.punches.enableAll();
var Raven = require('raven-js');

var osfHelpers = require('js/osfHelpers');
var CommentPane = require('js/commentpane');
var markdown = require('js/markdown');
var waterbutler = require('./waterbutler');

var nodeApiUrl = window.contextVars.node.urls.api;
var nodeId = window.contextVars.node.id;
var nodeUrl = '/' + nodeId + '/';

// Maximum length for comments, in characters
var MAXLENGTH = 500;
var MAXLEVEL = new Array();
MAXLEVEL['page'] = 10;
MAXLEVEL['pane'] = 5;
MAXLEVEL['widget'] = 5;

var TOGGLELEVEL = 2

var ABUSE_CATEGORIES = {
    spam: 'Spam or advertising',
    hate: 'Hate speech',
    violence: 'Violence or harmful behavior'
};

/*
 * Format UTC datetime relative to current datetime, ensuring that time
 * is in the past.
 */
var relativeDate = function(datetime) {
    var now = moment.utc();
    var then = moment.utc(datetime);
    then = then > now ? now : then;
    return then.fromNow();
};

var notEmpty = function(value) {
    return !!$.trim(value);
};

var exclusify = function(subscriber, subscribees) {
    subscriber.subscribe(function(value) {
        if (value) {
            for (var i=0; i<subscribees.length; i++) {
                subscribees[i](false);
            }
        }
    });
};

var exclusifyGroup = function() {
    var observables = Array.prototype.slice.call(arguments);
    for (var i=0; i<observables.length; i++) {
        var subscriber = observables[i];
        var subscribees = observables.slice();
        subscribees.splice(i, 1);
        exclusify(subscriber, subscribees);
    }
};

var BaseComment = function() {

    var self = this;
    self.abuseOptions = Object.keys(ABUSE_CATEGORIES);

    self._loaded = false;
    self.id = ko.observable();

    self.page = ko.observable('node'); // Default
    self.mode = 'pane'; // Default

    self.errorMessage = ko.observable();
    self.editErrorMessage = ko.observable();
    self.replyErrorMessage = ko.observable();

    self.replying = ko.observable(false);
    self.replyContent = ko.observable('');

    self.submittingReply = ko.observable(false);

    self.comments = ko.observableArray();
    self.unreadComments = ko.observable(0);

    self.pageNumber = ko.observable(0);

    self.level = -1;

    self.displayCount = ko.computed(function() {
        if (self.unreadComments() !== 0) {
            return self.unreadComments().toString();
        } else {
            return ' ';
        }
    });

    /* Removes number of unread comments from tab when comments pane is opened  */
    self.removeCount = function() {
        self.unreadComments(0);
    };

    self.replyNotEmpty = ko.computed(function() {
        return notEmpty(self.replyContent());
    });
    self.saveButtonText = ko.computed(function() {
        return self.submittingReply() ? 'Saving' : 'Comment';
    });

};

BaseComment.prototype.abuseLabel = function(item) {
    return ABUSE_CATEGORIES[item];
};

BaseComment.prototype.showReply = function() {
    this.replying(true);
};

BaseComment.prototype.cancelReply = function() {
    this.replyContent('');
    this.replying(false);
    this.submittingReply(false);
    this.replyErrorMessage('');
};

BaseComment.prototype.setupToolTips = function(elm) {
    $(elm).each(function(idx, item) {
        var $item = $(item);
        if ($item.attr('data-toggle') === 'tooltip') {
            $item.tooltip();
        } else {
            $item.find('[data-toggle="tooltip"]').tooltip({container: 'body'});
        }
    });
};

BaseComment.prototype.fetch = function(isCommentList, thread) {
    var self = this;
    var deferred = $.Deferred();
    if (self._loaded) {
        deferred.resolve(self.comments());
    }
    if (thread !== undefined) {
        return self.getThread(thread);
    }
    $.getJSON(
        nodeApiUrl + 'comments/',
        {
            page: self.page(),
            target: self.id(),
            rootId: self.rootId(),
            isCommentList: (isCommentList || null)
        },
        function(response) {
            self.comments(
                ko.utils.arrayMap(response.comments.reverse(), function (comment) {
                    return new CommentModel(comment, self, self.$root);
                })
            );
            if (isCommentList) {
                self.discussionByFrequency(response.discussionByFrequency);
                self.discussionByRecency(response.discussionByRecency);
            }
            self.unreadComments(response.nUnread);
            deferred.resolve(self.comments());
            self.checkFileExists();
            self._loaded = true;
        }
    );
    return deferred;
};

BaseComment.prototype.getThread = function(thread_id) {
    var self = this;
    var deferred = $.Deferred();
    if (self._loaded) {
        deferred.resolve(self.comments());
    }
    $.getJSON(
        nodeApiUrl + 'comment/' + thread_id + '/',
        {},
        function(response) {
            self.comments([]);
            self.comments.push(new CommentModel(response.comment, self, self.$root));
            deferred.resolve(self.comments());
            self._loaded = true;
        }
    );
    return deferred;
}

BaseComment.prototype.checkFileExists = function() {
    var self = this;
    var url;
    for (var c in self.comments()) {
        var comment = self.comments()[c];
        if (comment.page() !== 'files') {
            continue;
        }
        (function(comment) {
            url  = waterbutler.buildMetadataUrl(comment.title(), comment.provider(), nodeId, {}); // waterbutler url
            $.ajax({
                method: 'GET',
                url: url
            }).done(function(resp){
                console.log(resp); // todo change
            }).fail(function(xhl){
                console.log('error: '); // todo change
                console.log(xhl);
                comment.isHidden(true);
                $.map([self.$root.discussionByFrequency, self.$root.discussionByRecency], function(ls) {
                    var commenter_id = comment.author.id();
                    var ind;
                    for (var i in ls()) {
                        if (ls()[i].id == commenter_id) {
                            var commenter = ls()[i];
                            ind = i;
                            commenter.numOfComments -= 1;
                            if (commenter.numOfComments == 0) {
                                ls.splice(ind, 1);
                            }
                            break;
                        }
                    }
                });
            })
        })(comment);
    }
}

BaseComment.prototype.submitReply = function() {
    var self = this;
    if (!self.replyContent()) {
        self.replyErrorMessage('Please enter a comment');
        return;
    }
    // Quit if already submitting reply
    if (self.submittingReply()) {
        return;
    }
    self.submittingReply(true);
    osfHelpers.postJSON(
        nodeApiUrl + 'comment/',
        {
            page: self.page(),
            target: self.id(),
            content: self.replyContent(),
        }
    ).done(function(response) {
        self.cancelReply();
        self.replyContent(null);
        self.comments.unshift(new CommentModel(response.comment, self, self.$root));
        if (!self.hasChildren()) {
            self.hasChildren(true);
        }
        self.replyErrorMessage('');
        // Update discussion in case we aren't already in it
        var hasCommented = false;
        var discussion = self.$root.discussion();
        for (var i in discussion) {
            if (discussion[i].id == response.comment.id) {
                hasCommented = true;
                break;
            }
        }
        if (!hasCommented) {
            self.$root.discussionByRecency.unshift(response.comment.author);
            self.$root.discussionByFrequency.push(response.comment.author);
        }
        self.onSubmitSuccess(response);
        if (self.level >= self.MAXLEVEL) {
            window.location.href = nodeUrl + 'discussions/' + self.id();
        }
    }).fail(function() {
        self.cancelReply();
        self.errorMessage('Could not submit comment');
    });
};

var CommentModel = function(data, $parent, $root) {

    BaseComment.prototype.constructor.call(this);

    var self = this;

    self.$parent = $parent;
    self.$root = $root;

    // Note: assigns self.content()
    $.extend(self, ko.mapping.fromJS(data));

    self.contentDisplay = ko.observable(markdown.full.render(self.content()));

    // Update contentDisplay with rednered markdown whenever content changes
    self.content.subscribe(function(newContent) {
        self.contentDisplay(markdown.full.render(newContent));
    });

    self.dateCreated(data.dateCreated);
    self.dateModified(data.dateModified);

    self.prettyDateCreated = ko.computed(function() {
        return relativeDate(self.dateCreated());
    });
    self.prettyDateModified = ko.computed(function() {
        return 'Modified ' + relativeDate(self.dateModified());
    });

    self.mode = $parent.mode;
    self.MAXLEVEL = MAXLEVEL[self.mode];

    self.level = $parent.level + 1;

    self.showChildren = ko.observable(false);

    self.hoverContent = ko.observable(false);

    self.reporting = ko.observable(false);
    self.deleting = ko.observable(false);
    self.unreporting = ko.observable(false);
    self.undeleting = ko.observable(false);

    self.abuseCategory = ko.observable('spam');
    self.abuseText = ko.observable();

    self.editing = ko.observable(false);
    self.editVerb = self.modified ? 'edited' : 'posted';

    exclusifyGroup(
        self.editing, self.replying, self.reporting, self.deleting,
        self.unreporting, self.undeleting
    );

    self.isVisible = ko.computed(function() {
        return !self.isDeleted() && !self.isHidden() && !self.isAbuse();
    });

    self.editNotEmpty = ko.computed(function() {
        return notEmpty(self.content());
    });

    self.toggleIcon = ko.computed(function() {
            return self.showChildren() ? 'fa fa-minus-square-o' : 'fa fa-plus-square-o';
    });
    self.editHighlight = ko.computed(function() {
        return self.canEdit() && self.hoverContent() && self.mode !== 'widget';
    });
    self.canReport = ko.computed(function() {
        return self.$root.canComment() && !self.canEdit();
    });

    self.shouldShow = ko.computed(function() {
        if (!self.isDeleted() && !self.isHidden()) {
            return true;
        }
        if (self.isHidden()) {
            return self.level == 0;
        }
        return self.hasChildren() || self.canEdit();
    });

    self.shouldShowChildren = ko.computed(function() {
        if (self.isHidden()) {
            self.showChildren(false);
            return false;
        }
        return self.level < self.MAXLEVEL;
    });

    self.shouldContinueThread = ko.computed(function() {
        if (self.shouldShowChildren()) { return false;}
        return ((!self.isHidden()) && self.hasChildren());
    })

    self.cleanTitle = ko.computed(function() {
        var cleaned;
        switch(self.page()) {
            case 'wiki':
                cleaned = '(Wiki';
                if (self.title().toLowerCase() !== 'home') {
                    cleaned += ' - ' + self.title();
                }
                break;
            case 'files':
                cleaned = '(Files - ';
                var path = self.title().split('/');
                cleaned += path[path.length - 1];
                break;
            case 'node':
                cleaned = '(Overview';
                break;
        }
        cleaned += ')';
        return cleaned;
    });

    self.rootUrl = ko.computed(function(){
        var url = 'discussions';
        if (self.page() == 'node') {
            url = url + '/overview';
        } else {
            url = url + '/' + self.page();
        }
        return url;
    });

    self.parentUrl = ko.computed(function(){
        if (self.targetId() === self.rootId()) {
            return nodeUrl + self.rootUrl();
        }
        return '/' + self.targetId();
    });

    self.targetUrl = ko.computed(function(){
        if (self.page() == 'node') {
            return nodeUrl;
        } else if (self.page() == 'wiki') {
            return nodeUrl + self.page() + '/' + self.rootId();
        } else if (self.page() == 'files') {
            return '/' + self.rootId() + '/';
        }
    });

    if ((self.mode == 'pane' &&
        self.level < TOGGLELEVEL) ||
        (self.mode == 'page' &&
        self.level < self.MAXLEVEL)) {
        self.toggle();
    }

};

CommentModel.prototype = new BaseComment();

CommentModel.prototype.edit = function() {
    if (this.canEdit() && this.mode !== 'widget') {
        this._content = this.content();
        this.editing(true);
        this.$root.editors += 1;
    }
};

CommentModel.prototype.autosizeText = function(elm) {
    $(elm).find('textarea').autosize().focus();
};

CommentModel.prototype.cancelEdit = function() {
    this.editing(false);
    this.$root.editors -= 1;
    this.editErrorMessage('');
    this.hoverContent(false);
    this.content(this._content);
};

CommentModel.prototype.submitEdit = function(data, event) {
    var self = this;
    var $tips = $(event.target)
        .closest('.comment-container')
        .find('[data-toggle="tooltip"]');
    if (!self.content()) {
        self.errorMessage('Please enter a comment');
        return;
    }
    osfHelpers.putJSON(
        nodeApiUrl + 'comment/' + self.id() + '/',
        {content: self.content()}
    ).done(function(response) {
        self.content(response.content);
        self.dateModified(response.dateModified);
        self.editing(false);
        self.modified(true);
        self.editErrorMessage('');
        self.$root.editors -= 1;
        // Refresh tooltip on date modified, if present
        $tips.tooltip('destroy').tooltip();
    }).fail(function() {
        self.cancelEdit();
        self.errorMessage('Could not submit comment');
    });
};

CommentModel.prototype.reportAbuse = function() {
    this.reporting(true);
};

CommentModel.prototype.cancelAbuse = function() {
    this.abuseCategory(null);
    this.abuseText(null);
    this.reporting(false);
};

CommentModel.prototype.submitAbuse = function() {
    var self = this;
    osfHelpers.postJSON(
        nodeApiUrl + 'comment/' + self.id() + '/report/',
        {
            category: self.abuseCategory(),
            text: self.abuseText()
        }
    ).done(function() {
        self.isAbuse(true);
    }).fail(function() {
        self.errorMessage('Could not report abuse.');
    });
};

CommentModel.prototype.startDelete = function() {
    this.deleting(true);
};

CommentModel.prototype.submitDelete = function() {
    var self = this;
    $.ajax({
        type: 'DELETE',
        url: nodeApiUrl + 'comment/' + self.id() + '/',
    }).done(function() {
        self.isDeleted(true);
        self.deleting(false);
    }).fail(function() {
        self.deleting(false);
    });
};

CommentModel.prototype.cancelDelete = function() {
    this.deleting(false);
};

CommentModel.prototype.startUndelete = function() {
    this.undeleting(true);
};

CommentModel.prototype.submitUndelete = function() {
    var self = this;
    osfHelpers.putJSON(
        nodeApiUrl + 'comment/' + self.id() + '/undelete/',
        {}
    ).done(function() {
        self.isDeleted(false);
    }).fail(function() {
        self.undeleting(false);
    });
};

CommentModel.prototype.cancelUndelete = function() {
    this.undeleting(false);
};

CommentModel.prototype.startUnreportAbuse = function() {
    this.unreporting(true);
};

CommentModel.prototype.submitUnreportAbuse = function() {
    var self = this;
    osfHelpers.postJSON(
        nodeApiUrl + 'comment/' + self.id() + '/unreport/',
        {}
    ).done(function() {
        self.isAbuse(false);
    }).fail(function() {
        self.unreporting(false);
    });
};

CommentModel.prototype.cancelUnreportAbuse = function() {
    this.unreporting(false);
};

CommentModel.prototype.startHoverContent = function() {
    this.hoverContent(true);
};

CommentModel.prototype.stopHoverContent = function() {
    this.hoverContent(false);
};

CommentModel.prototype.toggle = function () {
    this.fetch(false);
    this.showChildren(!this.showChildren());
};

CommentModel.prototype.onSubmitSuccess = function() {
    this.showChildren(true);
};

/*
    *
    */
var CommentListModel = function(userName, host_page, host_name, mode, canComment, hasChildren, thread) {

    BaseComment.prototype.constructor.call(this);

    var self = this;

    self.$root = self;
    self.MAXLENGTH = MAXLENGTH;

    self.mode = mode;
    self.MAXLEVEL = MAXLEVEL[self.mode];

    self.editors = 0;
    self.userName = ko.observable(userName);
    self.canComment = ko.observable(canComment);
    self.hasChildren = ko.observable(hasChildren);

    self.discussionByFrequency = ko.observableArray();
    self.discussionByRecency = ko.observableArray();
    self.byRecency = ko.observable(true); // Default sorting is by recency
    
    self.discussion = ko.computed(function(){
        if (self.byRecency()) {
            return self.discussionByRecency();
        } else {
            return self.discussionByFrequency();
        }
    })

    self.page(host_page);
    self.id = ko.observable(host_name);
    self.rootId = ko.observable(host_name);

    self.commented = ko.computed(function(){
        return self.comments().length > 0;
    });
    self.rootUrl = ko.computed(function(){
        if (self.comments().length == 0) {
            return '';
        }
        return self.comments()[0].rootUrl();
    });

    self.parentUrl = ko.computed(function() {
        if (self.comments().length == 0) {
            return '';
        }
        return self.comments()[0].parentUrl();
    });

    self.recentComments = ko.computed(function(){
        var comments = [];
        for (var c in self.comments()) {
            var comment = self.comments()[c];
            if (comment.isVisible()) {
                comments.push(comment);
            }
            if (comments.length == 5) {
                break;
            }
        }
        return comments;
    });


    self.fetch(true, thread);

};

CommentListModel.prototype = new BaseComment();

CommentListModel.prototype.onSubmitSuccess = function() {};

CommentListModel.prototype.showRecent = function() {
    this.byRecency(true);
}

CommentListModel.prototype.showFrequent = function() {
    this.byRecency(false);
}

CommentListModel.prototype.initListeners = function() {
    var self = this;
    $(window).on('beforeunload', function() {
        if (self.editors) {
            return 'Your comments have unsaved changes. Are you sure ' +
                'you want to leave this page?';
        }
    });
};

var timestampUrl = nodeApiUrl + 'comments/timestamps/';
var onOpen = function(host_page, host_name) {
    var request = osfHelpers.putJSON(
        timestampUrl,
        {
            page: host_page,
            rootId: host_name
        }
    );
    request.fail(function(xhr, textStatus, errorThrown) {
        Raven.captureMessage('Could not update comment timestamp', {
            url: timestampUrl,
            textStatus: textStatus,
            errorThrown: errorThrown
        });
    });
};

var init = function(selector, host_page, host_name, mode, userName, canComment, hasChildren, thread_id) {

    new CommentPane(selector, host_page, host_name, mode, {onOpen: onOpen});
    var viewModel = new CommentListModel(userName, host_page, host_name, mode, canComment, hasChildren, thread_id);
    var $elm = $(selector);
    if (!$elm.length) {
        throw('No results found for selector');
    }
    osfHelpers.applyBindings(viewModel, $elm[0]);
    viewModel.initListeners();

    return viewModel;
};

module.exports = {
    init: init
};
