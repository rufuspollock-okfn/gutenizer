"""Various useful functionality related to Project Gutenberg

Gutenberg Index and URLs
========================

http://www.gutenberg.org/dirs/GUTINDEX.ALL

def get_etext_url(number):
    [[TODO: DOES NOT WORK]]
    Get the url for an etext given its number.
    This is non-trivial and follows instructions at start of GUTINDEX.ALL
    baseUrl = 'http://www.gutenberg.org/dirs/'
    ss = ''
    if number > 10000:
        ss = str(number)
        for char in ss[:-1]:
            pass
    if number <= 10000:
        raise 'Cannot deal with etext numbers less than 10000'
    return ss
"""
import os
import StringIO

import re
headerEndPhrases = [
        "Project Gutenberg's Etext of",
        'This etext was prepared by',
        'END.*THE SMALL PRINT',
        'START OF THIS PROJECT GUTENBERG',
        ]
notesStartPhrases = ["Executive Director's Notes:"]
notesEndPhrases = ['David Reed']
footerStartPhrases = ['End of Project Gutenberg', 'End of The Project Gutenberg'
    ]

class GutenbergCleaner(object):
    '''Clean up Gutenberg texts by removing all the header and footer bumpf.

    Usage: init and then run extract_text.

    TODO: deal with 'Produced by ' which occurs in both header and footer (and
    so cannot be dealt with by the usual methods).
    '''
    
    def __init__(self, etext):
        """
        @param etext: file like object containing the etext
        
        Procedure:
            1. strip out header and footer bumpf
            2. are there notes? If so strip them out
        """
        self.etext = etext
        # most texts are either ascii or latin-1
        self.etextStr = unicode(self.etext.read(), 'latin-1').encode('utf-8')
        # normalize the line endings to save us grief later
        self.etextStr = self.etextStr.replace('\r\n', '\n')
        self.hasNotes = False

    @classmethod
    def make_re_from_phrase(self, phrase):
        """
        Make a regular expression that matches a phrase and its surrounding
        paragraph, i.e. that look like:
        
        ... phrase ....
        more text
        [blank]
        [blank]+
        """
        paragraphText = '(^.+\w.+\n)*' # need \S to ensure not just whitespace
        # [[TODO: check slowdown due to inclusion of '^.*' at start
        tmp = '^.*' + phrase + '.*\n' + paragraphText + '\s+'
        return re.compile(tmp, re.I | re.M)  # make it case insensitive
    
    def _find_max(self, phrase, string):
        maxIndex = 0
        regex = self.make_re_from_phrase(phrase)
        matches = regex.finditer(string)
        for match in matches:
            maxIndex = max(match.end(), maxIndex)
        return maxIndex
    
    def _find_min(self, phrase, string):
        minIndex = len(string)
        regex = self.make_re_from_phrase(phrase)
        matches = regex.finditer(string)
        for match in matches:
            minIndex = min(match.start(), minIndex)
        return minIndex
    
    def extract_text(self):
        """Extract the core text.
        """
        self.notesEnd = self.get_notes_end()
        self.headerEnd = self.get_header_end()
        self.footerStart = self.get_footer_start()
        startIndex = self.headerEnd
        if self.notesEnd > 0:
            startIndex = self.notesEnd
        return self.etextStr[startIndex : self.footerStart].rstrip()
        
    def get_notes_end(self):
        "Return 0 if no notes"
        indices = [ self._find_max(phrase, self.etextStr) for phrase in notesEndPhrases]
        index = max(indices)
        return index
    
    def get_header_end(self):
        indices = [ self._find_max(phrase, self.etextStr) for phrase in headerEndPhrases]
        return max(indices)
    
    def get_footer_start(self):
        indices = [ self._find_min(phrase, self.etextStr) for phrase in footerStartPhrases]
        return min(indices)

import sys
import urllib2
if __name__ == '__main__':
    if len(sys.argv) < 2:
        msg = 'You need to provide the url of a Gutenberg text, e.g.:\n\n'
        msg += 'python gutenberg.py http://www.gutenberg.org/dirs/etext00/0ws2510.txt'
        print msg
        sys.exit(0)

    url = sys.argv[1]
    # Gutenberg seems to prevent access by anything that isn't "human" - we are
    # not a bot though so ...
    headers = { 'User-Agent' : '"Mozilla/4.0 (compatible; MSIE 5.01; Windows NT 5.0)"' }
    req = urllib2.Request(url, None, headers)
    fileobj = urllib2.urlopen(req)
    # print 'Loaded: %s' % url
    cleaner = GutenbergCleaner(fileobj)
    print cleaner.extract_text()

