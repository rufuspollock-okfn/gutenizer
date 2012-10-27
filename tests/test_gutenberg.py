import gutenberg as G
import urllib

class TestFormat:
    
    def test_make_re_from_phrase(self):
        outStr = """blah
            
            
            """
        inStr = outStr + 'All is Well that'
        regex = G.GutenbergCleaner.make_re_from_phrase('blah')
        out = regex.search(inStr)
        assert out.group() == outStr
    
    def test_make_re_from_phrase_2(self):
        outStr = """blah
            joe
            hello
            
            
            """
        inStr = outStr + 'All is Well that'
        regex = G.GutenbergCleaner.make_re_from_phrase('blah')
        out = regex.search(inStr)
        assert out.group() == outStr
    
    def test_make_re_from_phrase_3(self):
        tomatch = 'Produced by '
        instr = '''Produced by Dianne Bean


CAMILLE (LA DAME AUX CAMILIAS)
'''
        regex = G.GutenbergCleaner.make_re_from_phrase(tomatch)
        out = regex.search(instr).group()
        assert not 'CAMILLE' in out, out
        assert 'Produced by Dianne' in out, out
        

class TestGutenbergCleaner:
    # As you like it in Folio and normal
    # url1 = 'http://www.gutenberg.org/dirs/etext00/0ws2510.txt'
    # url2 = 'http://www.gutenberg.org/dirs/etext98/2ws2510.txt'
    # etext1 = urllib.urlopen(url1)
    # etext2 = urllib.urlopen(url2)
    etext1 = open('tests/data/0ws2510.txt')
    etext2 = open('tests/data/2ws2510.txt')
    gut1 = G.GutenbergCleaner(etext1)
    gut2 = G.GutenbergCleaner(etext2)
    
    def test_get_header_end(self):
        out = self.gut1.get_header_end()
        exp = self.gut1.etextStr.index("Executive Director's Notes:")
        assert out == exp
    
    def test_get_footer_start(self):
        out = self.gut1.get_footer_start()
        # has no footer 
        exp = len(self.gut1.etextStr)
        assert out == exp
        
        out = self.gut2.get_footer_start()
        print self.gut2.etextStr
        exp = self.gut2.etextStr.index("End of Project Gutenberg Etext of As You Like It by Shakespeare")
        assert out == exp
    
    def test_get_notes_end(self):
        out = self.gut1.get_notes_end()
        exp = self.gut1.etextStr.index("As you Like it\n\nActus")
        assert out == exp

    def test_extract_text(self):
        # [[TODO: run this test on all of the etexts]]
        for gut in [self.gut1, self.gut2]:
            out = gut.extract_text()
            notFound = (out.find('Gutenberg') == -1)
            assert notFound

