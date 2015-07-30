var $ = require('jquery');
var m = require('mithril');
var mime = require('js/mime');
var bootbox = require('bootbox');
var $osf = require('js/osfHelpers');
var waterbutler = require('js/waterbutler');

// Local requires
var utils = require('./util.js');
var FileEditor = require('./editor.js');
var FileRevisionsTable = require('./revisions.js');

// Sanity
var Panel = utils.Panel;


var EDITORS = {'text': FileEditor};

var FileViewPage = {
    controller: function(context) {
        var self = this;
        self.context = context;
        self.file = self.context.file;
        self.node = self.context.node;
        self.editorMeta = self.context.editor;
        //Force canEdit into a bool
        self.canEdit = m.prop(!!self.context.currentUser.canEdit);

        $.extend(self.file.urls, {
            delete: waterbutler.buildDeleteUrl(self.file.path, self.file.provider, self.node.id),
            metadata: waterbutler.buildMetadataUrl(self.file.path, self.file.provider, self.node.id),
            revisions: waterbutler.buildRevisionsUrl(self.file.path, self.file.provider, self.node.id),
            content: waterbutler.buildDownloadUrl(self.file.path, self.file.provider, self.node.id, {accept_url: false, mode: 'render'})
        });

        $(document).on('fileviewpage:delete', function() {
            bootbox.confirm({
                title: 'Delete file?',
                message: '<p class="overflow">' +
                        'Are you sure you want to delete <strong>' +
                        self.file.safeName + '</strong>?' +
                    '</p>',
                callback: function(confirm) {
                    if (!confirm) {
                        return;
                    }
                    $.ajax({
                        type: 'DELETE',
                        url: self.file.urls.delete,
                        beforeSend: $osf.setXHRAuthorization
                    }).done(function() {
                        window.location = self.node.urls.files;
                    }).fail(function() {
                        $osf.growl('Error', 'Could not delete file.');
                    });
                },
                buttons:{
                    confirm:{
                        label:'Delete',
                        className:'btn-danger'
                    }
                }
            });
        });

        $(document).on('fileviewpage:download', function() {
            window.location = self.file.urls.content;
            return false;
        });

        self.shareJSObservables = {
            activeUsers: m.prop([]),
            status: m.prop('connecting'),
            userId: self.context.currentUser.id
        };

        self.editHeader = function() {
            return m('.row', [
                m('.col-sm-12', m('span[style=display:block;]', [
                    m('h3.panel-title',[m('i.fa.fa-pencil-square-o'), '   Edit ']),
                    m('.pull-right', [
                        m('.progress.no-margin.pointer', {
                            'data-toggle': 'modal',
                            'data-target': '#' + self.shareJSObservables.status() + 'Modal'
                        }, [
                            m('.progress-bar.p-h-sm.progress-bar-success', {
                                connected: {
                                    style: 'width: 100%',
                                    class: 'progress-bar progress-bar-success'
                                },
                                connecting: {
                                    style: 'width: 100%',
                                    class: 'progress-bar progress-bar-warning progress-bar-striped active'
                                },
                                saving: {
                                    style: 'width: 100%',
                                    class: 'progress-bar progress-bar-info progress-bar-striped active'
                                }
                            }[self.shareJSObservables.status()] || {
                                    style: 'width: 100%',
                                    class: 'progress-bar progress-bar-danger'
                                }, [
                                    m('span.progress-bar-content', [
                                        {
                                            connected: 'Live editing mode ',
                                            connecting: 'Attempting to connect ',
                                            unsupported: 'Unsupported browser ',
                                            saving: 'Saving... '
                                        }[self.shareJSObservables.status()] || 'Unavailable: Live editing ',
                                        m('i.fa.fa-question-circle.fa-large')
                                    ])
                                ])
                            ])
                        ])
                    ]))
                ]);
        };


        // Hack to delay creation of the editor
        // until we know this is the current file revsion
        self.enableEditing = function() {
            // Sometimes we can get here twice, check just in case
            if (self.editor || !self.canEdit()) {
                m.redraw(true);
                return;
            }
            var fileType = mime.lookup(self.file.name.toLowerCase());
            // Only allow files < 1MB to be editable
            if (self.file.size < 1048576 && fileType) { //May return false
                var editor = EDITORS[fileType.split('/')[0]];
                if (editor) {
                    self.editor = new Panel('Edit', self.editHeader, editor, [self.file.urls.content, self.file.urls.sharejs, self.editorMeta, self.shareJSObservables], false);
                }
            }
            m.redraw(true);
        };

        //Hack to polyfill the Panel interface
        //Ran into problems with mithrils caching messing up with multiple "Panels"
        self.revisions = m.component(FileRevisionsTable, self.file, self.node, self.enableEditing, self.canEdit);
        self.revisions.selected = false;
        self.revisions.title = 'Revisions';

        // inform the mfr of a change in display size performed via javascript,
        // otherwise the mfr iframe will not update unless the document windows is changed.
        self.triggerResize = $osf.throttle(function () {
            $(document).trigger('fileviewpage:resize');
        }, 1000);

        self.mfrIframeParent = $('#mfrIframeParent');
    },
    view: function(ctrl) {
        //This code was abstracted into a panel toggler at one point
        //it was removed and shoved here due to issues with mithrils caching and interacting
        //With other non-mithril components on the page
        var panels;
        if (ctrl.editor) {
            panels = [ctrl.editor, ctrl.revisions];
        } else {
            panels = [ctrl.revisions];
        }

        var shown = panels.reduce(function(accu, panel) {
            return accu + (panel.selected ? 1 : 0);
        }, 0);

        var panelsShown = shown + (ctrl.mfrIframeParent.is(':visible') ? 1 : 0);
        var mfrIframeParentLayout;
        var fileViewPanelsLayout;

        if (panelsShown === 3) {
            // view | edit | revisions
            mfrIframeParentLayout = 'col-sm-4';
            fileViewPanelsLayout = 'col-sm-8';
        } else if (panelsShown === 2) {
            if (ctrl.mfrIframeParent.is(':visible')) {
                if (ctrl.revisions.selected) {
                    // view | revisions
                    mfrIframeParentLayout = 'col-sm-8';
                    fileViewPanelsLayout = 'col-sm-4';
                } else {
                    // view | edit
                    mfrIframeParentLayout = 'col-sm-6';
                    fileViewPanelsLayout = 'col-sm-6';
                }
            } else {
                // edit | revisions
                mfrIframeParentLayout = '';
                fileViewPanelsLayout = 'col-sm-12';
            }
        } else {
            // view
            if (ctrl.mfrIframeParent.is(':visible')) {
                mfrIframeParentLayout = 'col-sm-12';
                fileViewPanelsLayout = '';
            } else {
                // edit or revisions
                mfrIframeParentLayout = '';
                fileViewPanelsLayout = 'col-sm-12';
            }
        }
        $('#mfrIframeParent').removeClass().addClass(mfrIframeParentLayout);
        $('.file-view-panels').removeClass().addClass('file-view-panels').addClass(fileViewPanelsLayout);

        m.render(document.getElementById('toggleBar'), m('.btn-toolbar.m-t-md', [
            ctrl.canEdit() ? m('.btn-group.m-l-xs.m-t-xs', [
                m('.btn.btn-sm.btn-danger.file-delete', {onclick: $(document).trigger.bind($(document), 'fileviewpage:delete')}, 'Delete')
            ]) : '',
            m('.btn-group.m-t-xs', [
                m('#sharebutton.btn.btn-sm.btn-primary', {onclick: function () {
                    var link = $('iframe').attr('src');
                    var height = $('iframe').attr('height');
                    $('#height').val(height);
                    updateHeight();
                }, config: function(element, isInitialized) {
                    if(!isInitialized){
                        var button = $(element).popover();
                        button.on('show.bs.popover', function(e){
                            button.data()['bs.popover'].$tip.css('max-width', '600px').css('text-align', 'center');
                        });
                        if (!window.contextVars.node.isPublic) {
                            $('#sharebutton').attr('disabled', 'disabled');
                        }
                        else {
                            $('#sharebutton').removeAttr('disabled', 'disabled');
                        }
                        var link = $('iframe').attr('src');
                        var height = $('iframe').attr('height');
                        link = link.substring(0, link.indexOf('download') + 8);
                        var url = link.substring(0, link.indexOf('render'));
                        var style = '\<link href=\"' + url + 'static/css/mfr.css\" media=\"all\" rel=\"stylesheet\" /\>';
                        var data = [
                            '\<ul class="nav nav-tabs nav-justified"\>',
                            '   \<li class="active"\>\<a href="#share" data-toggle="tab"\>Share\</a\>\</li\>', '' +
                            '   \<li\>\<a href="#embed" data-toggle="tab"\>Embed\</a\>\</li\>',
                            '\</ul\>\<br\>',
                            '\<div class="tab-content"\>',
                            '   \<div id="share" class="tab-pane fade in active"\>',
                            '       \<input onclick="this.select()" class="form-control" type="text" value="' + link + '" /\>',
                            '   \</div\>',
                            '   \<div id="embed" class="tab-pane fade"\>',
                            '       \<p data-toggle="tooltip" data-placement="bottom" title="Copy and paste to dynamically render an iFrame that is automatically sized appropriately."\>CSS Style, HTML & Script\<p/\>',
                            '       \<textarea onclick="this.select()" class="form-control" \>'
                                        + style + '\n'
                                        + '\<div id="mfrIframe" class="mfr mfr-file"\>\</div\> \n',
                                        '\<script src="' + url + 'static/js/mfr.js"\>\</script\> \n',
                                        '\<script\> \n',
                                        '   var mfrRender = new mfr.Render\("mfrIframe", "' + link + '"\);\n',
                                        '\</script\> ',
                            '       \</textarea\>',
                            '       \<br/\> \<p data-toggle="tooltip" data-placement="bottom" title="Copy and paste to directly embed the iFrame with custom sizing and scrolling enabled."\>Direct iFrame\<p/\>',
                            '           \<textarea id="directIFrame" onclick="this.select()" class="form-control" \>'
                                            + '\<iframe src="' + link + '" width="100%" scrolling="yes" height="100%" marginheight="0" frameborder="0" allowfullscreen webkitallowfullscreen \>',
                            '           \</textarea\> \<br\>',
                            '       \<div class="collapse-group"\> \<div class="form-horizontal collapse" aria-expanded="false"\> \<div class="form-group"\> ',
                            '           \<label class="sr-only col-sm-2" for="width"\>Width\</label\> \<div class="col-sm-4 col-sm-offset-4"\> \<div class="input-group"\>',
                            '               \<span class="input-group-addon"\> Width \</span\> \<input type="text" class="form-control text-center" id="width" placeholder="100%" onchange="updateWidth()"\> \</div\> \</div\> \</div\> \<div class="form-group"\> ',
                            '           \<label class="sr-only col-sm-2" for="height"\>Height\</label\> \<div class="col-sm-4 col-sm-offset-4"\> \<div class="input-group"\> ',
                            '               \<span class="input-group-addon"\>Height\</span\> \<input type="text" class="form-control text-center" id="height" placeholder="100%" onchange="updateHeight()"\> \</div\>',
                            '       \</div\> \</div\> \</div\>',
                            '       \<a class="btn btn-default" id="showmore"\>Show More\</a\> ',
                            '\</div\> \</div\> \</div\> ',
                            '\<script\> $(\'#showmore\').on(\'click\', function(e) {e.preventDefault();var $this = $(this);var $collapse = $this.closest(\'.collapse-group\').find(\'.collapse\');$collapse.collapse(\'toggle\'); if($(\'#showmore\').text() === "Show More") { $(\'#showmore\').text("Show Less"); } else { $(\'#showmore\').text("Show More"); } }); function updateWidth() { var str = $(\'#directIFrame\').html().replace(/width=(".*?")/, \'width="\' + $(\'#width\').val() +  \'"\'); $(\'#directIFrame\').html(str); } function updateHeight() { var str = $(\'#directIFrame\').html().replace(/height=(".*?")/, \'height="\' + $(\'#height\').val() +  \'"\'); $(\'#directIFrame\').html(str); } \</script\>',
                        ].join('');
                        $(element).attr('data-content', data);
                    }
                }, 'data-toggle': 'popover', 'data-placement': 'bottom', 'data-content': 'Content', 'title': 'Share', 'data-container': 'body', 'data-html': 'true'}, 'Share')
            ].concat(
                m('.btn.btn-sm.btn-primary.file-download', {onclick: $(document).trigger.bind($(document), 'fileviewpage:download')}, 'Download')
            )),
            m('.btn-group.btn-group-sm.m-t-xs', [
                m('.btn.btn-default.disabled', 'Toggle view: ')
            ].concat(
                m('.btn' + (ctrl.mfrIframeParent.is(':visible') ? '.btn-primary' : '.btn-default'), {
                    onclick: function (e) {
                        e.preventDefault();
                        // atleast one button must remain enabled.
                        if (!ctrl.mfrIframeParent.is(':visible') || panelsShown > 1) {
                            ctrl.mfrIframeParent.toggle();
                        }
                    }
                }, 'View')
            ).concat(
                panels.map(function(panel) {
                    return m('.btn' + (panel.selected ? '.btn-primary' : '.btn-default'), {
                        onclick: function(e) {
                            e.preventDefault();
                            // atleast one button must remain enabled.
                            if (!panel.selected || panelsShown > 1) {
                                panel.selected = !panel.selected;
                            }
                        }
                    }, panel.title);
                })
            ))
        ]));

        return m('.file-view-page', m('.panel-toggler', [
            m('.row', panels.map(function(pane, index) {
                ctrl.triggerResize();
                if (!pane.selected) {
                    return m('[style="display:none"]', pane);
                }
                return m('.col-sm-' + Math.floor(12/shown), pane);
            }))
        ]));
    }
};


module.exports = function(context) {
    // Treebeard forces all mithril to load twice, to avoid
    // destroying the page iframe this out side of mithril.
    if (!context.file.urls.render) {
        $('#mfrIframe').html(context.file.error);
    } else {
        var url = context.file.urls.render;
        if (context.accessToken) {
            url += '&token=' + context.accessToken;
        }

        if (window.mfr !== undefined) {
            var mfrRender = new mfr.Render('mfrIframe', url);
            $(document).on('fileviewpage:reload', function() {
                mfrRender.reload();
            });
            $(document).on('fileviewpage:resize', function() {
                mfrRender.resize();
            });
        }

    }

    return m.component(FileViewPage, context);
};
