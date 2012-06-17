"""Various useful functionality related to Project Gutenberg
"""
import os
import StringIO

class GutenbergIndexBase(object):
    """Parse the index of Gutenberg works.

    TODO: Gutenberg now make available the index in RDF/XML form:
    http://www.gutenberg.org/feeds/catalog.rdf.bz2 and we should try to use
    that instead of plain text file
    """
    
    # url for the Gutenberg index file
    gutindex = 'http://www.gutenberg.org/dirs/GUTINDEX.ALL'

    def __init__(self, cache):
        self.cache = cache
        self.download_gutenberg_index()
        self._gutindex_local_path = self.cache.path(self.gutindex)

    def download_gutenberg_index(self):
        """Download the Gutenberg Index file GUTINDEX.ALL to cache if we don't
        have it already.
        """
        self.cache.download_url(self.gutindex)

    def make_url(self, year, idStr):
        return 'http://www.gutenberg.org/dirs/etext%s/%s10.txt' % (year[2:], idStr)

    def get_relevant_works(self):
        # implement in derived class 
        raise NotImplementedError

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


#def get_etext_url(number):
#    """
#    [[TODO: DOES NOT WORK]]
#    Get the url for an etext given its number.
#    This is non-trivial and follows instructions at start of GUTINDEX.ALL
#    """
#    baseUrl = 'http://www.gutenberg.org/dirs/'
#    ss = ''
#    if number > 10000:
#        ss = str(number)
#        for char in ss[:-1]:
#            pass
#    if number <= 10000:
#        raise 'Cannot deal with etext numbers less than 10000'
#    return ss


class HelperBase(object):

    def __init__(self, works, cache, verbose=False):
        '''
        @param works: list of works (from e.g. GutenbergIndex.get_relevant_works)
        '''
        self.verbose = verbose
        self.cache = cache
        self._index = works

    def vprint(self, info, force=True):
        if self.verbose or force:
            print(info)
     
    def _filter_index(self, line):
        """Filter items in index return only those whose id (url) is in line.
        If line is empty or None return all items
        """
        if line:
            textsToAdd = []
            textsUrls = line.split()
            for item in self._index:
                if item[1] in textsUrls:
                    textsToAdd.append(item)
            return textsToAdd
        else:
            return self._index

    def execute(self, line=None):
        self.download(line)
        self.clean(line)
        self.add_to_db()

    def download(self, line=None):
        """Download from Project Gutenberg all the texts wanted. 
        """
        for item in self._index:
            title = item[0]
            url = item[1]
            if self.verbose:
                print 'Downloading %s (%s)' % (url, title)
            self.cache.download_url(item[1])
    
    def title_to_name(self, title):
        """Convert a title to a unique name
        """
        tmp1 = title.replace(',', '')
        tmp1 = tmp1.replace("'", '')
        tmp1 = tmp1.lower()
        # TODO: is 'king' too shakespeare specific ?
        stripwords = [ 'king ', 'a ', 'the ' ]
        for ww in stripwords:
            if tmp1.startswith(ww):
                tmp1 = tmp1[len(ww):]
        tmp1 = tmp1.strip()
        tmp1 = tmp1.replace(' ', '_')
        return tmp1

    def clean(self, line=None):
        """Clean up raw gutenberg texts to extract underlying work (so remove
        all extra bumpf such as Gutenberg licence, contributor info etc).
        
        Texts are written to same directory as original file with 'cleaned'
        prepended to their name.
        
        @param line: space separated list of text urls: text-url text-url
        """
        # implement in inheriting class
        pass

    def add_to_db(self):
        """Add all gutenberg texts to the db list of texts.
        
        Stubbed: override in inheriting class.
        """
        pass
