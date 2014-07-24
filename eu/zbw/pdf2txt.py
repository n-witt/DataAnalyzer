from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from cStringIO import StringIO

def pdf_to_txt(path, lowerBorder=-1, upperBorder=-1):
   rsrcmgr = PDFResourceManager()
   retstr = StringIO()
   codec = 'utf-8'
   laparams = LAParams()
   device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
   fp = file(path, 'rb')
   interpreter = PDFPageInterpreter(rsrcmgr, device)
   password = ""
   maxpages = 0
   caching = True
   if lowerBorder==-1 and upperBorder==-1:
      pagenos=set()
   else:
      if lowerBorder==-1 or upperBorder==-1 or lowerBorder > upperBorder:
         raise ValueError("illegal parameter passed")
      else:
         pagenos=set(range(lowerBorder, upperBorder+1))
   for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
      interpreter.process_page(page)
   fp.close()
   device.close()
   s = retstr.getvalue()
   retstr.close()
   return s.decode('utf-8')