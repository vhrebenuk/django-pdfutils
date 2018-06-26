# -*- coding: utf-8 -*-

import os
import posixpath
import sys
import tempfile

try:
    from urllib.parse import unquote
except ImportError:     # Python 2
    from urllib import unquote

from django.conf import settings
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.views.generic import TemplateView

from pdfutils.utils import generate_pdf, unique


class ReportBase(TemplateView):
    title = u'Untitled report'
    orientation = 'portrait'

    def __init__(self):
        self.__styles = ['pdfutils/css/base.css']

    def filename(self):
        return 'Untitled-document.pdf'

    def get_format(self):
        return self.request.GET.get('format', 'pdf')

    def get_context_data(self):
        self.context = {
            'title': self.title,
            'slug': self.slug,
            'user': self.request.user,
            'orientation': self.orientation,
            'MEDIA_URL': settings.MEDIA_URL,
            'STATIC_URL': settings.STATIC_URL,
            'STYLES': self.render_styles(),
        }
        return self.context

    def add_styles(self, styles):
        self.__styles = []

        for style in styles:
            self.__styles.append(style)

    def get_styles(self):
        if self.orientation == 'portrait':
            self.__styles.append('pdfutils/css/portrait.css')
        else:
            self.__styles.append('pdfutils/css/landscape.css')
        self.__styles = unique(self.__styles)
        return self.__styles

    def render_styles(self):
        """
        Eventually this should return a list of <link /> tags
        instead of inline styles. xhtml2pdf has a weird bug
        which prevents external stylesheet from working.
        """
        out = []
        for style in self.get_styles():
            path = style
            normalized_path = posixpath.normpath(unquote(path)).lstrip('/')
            absolute_path = finders.find(normalized_path)
            if absolute_path:
                with open (absolute_path, "r") as fd:
                    out.append(fd.read())
            else:
                print "[pdfutils error] File not found: %s" % style
        return '<style>%s</style>' % ''.join(out)

    def render_to_file(self):
        """
        Renders a PDF report to a temporary file
        """
        return generate_pdf(self.template_name, context=self.get_context_data())

    def render(self):
        """
        Renders a PDF report to the HttpRequest object
        """
        ctx = self.get_context_data()
        self.response = HttpResponse(
                content_type='application/pdf; name=%s' % self.filename())

        generate_pdf(self.template_name, \
                file_object=self.response, context=ctx)

        self.response['Content-Disposition'] = 'inline; filename=%s' % \
                self.filename()

        return self.response

    def get(self, request, *args, **kwargs):
        if self.get_format() == 'pdf':
            return self.render()
        return super(ReportBase, self).get(request, *args, **kwargs)


class Report(ReportBase):
    pass
