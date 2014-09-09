'''
Created on 17.07.2014

@author: user
'''
from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError 
import bisect
from fuzzywuzzy import process
from os import listdir
from os.path import isfile, join
from pdfminer.pdfdocument import PDFTextExtractionNotAllowed
import re
import requests
import sys, codecs, locale
import urllib

from pdf2txt import pdf_to_txt


def main():
   sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)
   mypath = u'../../samples'
   min_tokens = 2
   onlypdfFiles = [ f for f in listdir(mypath) if isfile(join(mypath,f)) ]
   qualityThreshold = 80
   overallResult = []
   for f in onlypdfFiles:
      print f
      try:
         pdfFile = PdfFileReader(open(mypath + '/' + f, "rb"))
         if pdfFile.isEncrypted:
            pdfFile.decrypt('')
         metainfo = pdfFile.getDocumentInfo()
         res = []
         hit = []
         bestHit = []
         title = None
         author = None
         
         #in case there are some metadata
         if metainfo != None:
            #removing useless (since they are too short) terms         
            if metainfo.title != None:
               title = removeShortTerms([metainfo.title], 5)
               if title == []:
                  title = None
               else:
                  title = title[0]
            if metainfo.author != None:   
               author = removeShortTerms([metainfo.author], 5)
               if author == []:
                  author = None
               else:
                  author = author[0]
                        
            #in case there are author and/or title information in the metadata
            if (author != None or title != None):
               if author != None and title != None:            
                  query = ('title', title),('person', author)
               else:
                  if author != None:
                     query = (('person', author),)
                  if title != None:
                     query = (('title', title),)
               res = searchDataprovider(query)
               if res['hits']['total'] > 0:
                  bestHit = selectBestMatch([q[1] for q in query], res['hits']['hits'], qualityThreshold, creatorWeight=1, titleWeight=1)
                  if bestHit != None:
                     participants = getParticipants(bestHit[1])
                     overallResult.append({'match': True, 'quality': bestHit[0], 'filename': f, 'id': bestHit[1]['id'],
                                           'participants': [a for a in participants if len(participants) > 0], 
                                           'title': bestHit[1]['title']})                  
         
         # when there are no metainfomation available or
         # there where no decent results
         if bestHit == [] or bestHit == None:
            hits = []
            s = pdf_to_txt(mypath + '/' + f, 0, 0)
            paragraphs = re.split(' *\n+ *', s)
            paragraphs = removeShortTerms(paragraphs, 5)
            end = min(5, len(paragraphs))
            for a in range(0, end):
               #search only if there are more than min_tokens words
               if len(paragraphs[a].split()) > min_tokens:
                  res = searchDataprovider((('title', paragraphs[a]),))
                  if res != None and res['hits']['total'] > 0:
                     hit = selectBestMatch(paragraphs, res['hits']['hits'], qualityThreshold)
                     if hit != None:
                        bisect.insort_left(hits, hit)
            if len(hits) > 0:
               bestHit = hits[-1]
               #creator, person, contributor etc. unionizen und in authos unterbringen
               participants = getParticipants(bestHit[1])
               overallResult.append({'match': True, 'quality': bestHit[0], 'filename': f, 'id': bestHit[1]['id'],
                                'participants': [a for a in participants if len(participants) > 0], 
                                'title': bestHit[1]['title']})
            else:
               overallResult.append({'match': False, 'reason': 'no match', 'filename': f})
      except (AttributeError, PdfReadError, IOError, AssertionError, KeyError, NotImplementedError, PDFTextExtractionNotAllowed, TypeError) as e:
         print "exception:"
         for arg in e.args:
            print arg
         overallResult.append({'match': False, 'reason': 'exception', 'filename': f})
   print("done. Results:")
   for i, r in enumerate(overallResult):
      if r['match'] == True:
         print str(i) + '.' + ' match: True' + '\n' \
               '    quality: ' + str(r['quality']) + '\n' + \
               '    filename. ' + r['filename'] + '\n' + \
               '    id: ' + r['id'] + '\n' + '    title: ' + r['title']
         for p in r['participants']:
            print '    participant: ' + p
      else:
         print str(i) + '.' + ' match: False' + '\n' + \
               '   reason: ' + r['reason'] + '\n' + \
               '   filename: ' + r['filename']

def getParticipants(hit):
   creators = set()
   if hit.has_key('creator'):
      creators = creators.union(set(hit['creator']))
   if hit.has_key('person'):
      creators = creators.union(set(hit['person']))
   if hit.has_key('contributor'):
      creators = creators.union(set(hit['contributor']))
   if hit.has_key('publisher'):
      creators = creators.union(set(hit['publisher'])) 
   return creators

def removeShortTerms(l, length=5): 
   l = uniqify(l)
   removeCandidates = []
   for s in l:
      if len(s) < length:
         removeCandidates.append(s)
   for s in removeCandidates:
      l.remove(s)
   return l

def uniqify(seq): 
   seen = {}
   result = []
   for item in seq:
      if item in seen: continue
      seen[item] = 1
      result.append(item)
   return result
   
def selectBestMatch(tokens, hits, qualityThreshold=50, creatorWeight=2, titleWeight=1):
   results = []
   for hit in hits:
      try:
         creators = set()
         normalizedScore = 0
         creatorScore = 0
         score = 0
         if hit.has_key('title'):
            foo = process.extractBests(hit['title'], tokens)
            if len(foo) > 0:
               score += foo[0][1] * titleWeight
         if hit.has_key('creator'):
            creators = creators.union(set(hit['creator']))
         if hit.has_key('person'):
            creators = creators.union(set(hit['person']))
         if hit.has_key('contributor'):
            creators = creators.union(set(hit['contributor']))
         if hit.has_key('publisher'):
            creators = creators.union(set(hit['publisher']))            
            
         if len(creators) > 0:
            for creator in creators:
               foo = process.extractBests(creator, tokens)
               if foo != None and foo != []:
                  creatorScore += foo[0][1]
            score += (creatorScore/len(creators)) * creatorWeight

         normalizedScore = score/(creatorWeight+titleWeight)   
         if normalizedScore >= qualityThreshold:
            bisect.insort_left(results, (normalizedScore, hit))
      except UnicodeDecodeError as e:
         continue
   if len(results) > 0:
      return results[-1]
   return None

def min(max, objectLen):
   if objectLen > max:
      end = max
   else:
      end = objectLen
   return end
   
def printEconbizOutput(res):
   if res != None:
      for r in res:
         if r.has_key('title'):
            print "title: " + r['title']
         if r.has_key('creator'):
            for s in r['creator']:
               print "creator: " + s


def searchDataprovider(queries):
   allowedFields = ["accessRights", "date", "date_sort", "date_submission", "fulltext",
                   "id", "institution", "isPartOf", "isn", "jel", "language", "location",
                   "person", "publisher", "source", "subject", "text", "title", "type",
                   "type_genre"]
   queryString = ""
   assert isArray(queries)
   for e in queries:
      assert isArray(e)
      assert e[0] in allowedFields
      assert isinstance(e[1], (str, unicode))
      #replace non-alphanumeric and non-whitespace characters an assemble the query  
      queryString += e[0] + ':' + re.sub(r'[^(\d\w\s)]', '', e[1])
      f = 'https://api.econbiz.de/v1/search?q=' + urllib.quote_plus(queryString) +'&echo=on'
      
      response = requests.get(f)
      
      if response.status_code == 200:
         return response.json()
      else:
         return None
      
def isArray(var):
   return isinstance(var, (list, tuple))   
   
if __name__ == "__main__":
   main()