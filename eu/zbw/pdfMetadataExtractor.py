'''
Created on 17.07.2014

@author: user
'''
from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError 
from os import listdir
from os.path import isfile, join
import requests
from pdf2txt import pdf_to_txt
import re
from fuzzywuzzy import process
import bisect

def main():
   mypath = u'../../samples'
   min_tokens = 2
   onlypdfFiles = [ f for f in listdir(mypath) if isfile(join(mypath,f)) ]
   for f in onlypdfFiles:
      print "currently in progress: " + f
      try:
         pdfFile = PdfFileReader(open(mypath + '/' + f, "rb"))
         metainfo = pdfFile.getDocumentInfo()
         #in case there are autor and title information in the metadata
         if metainfo.author != None or metainfo.title != None:
            res = searchDataprovider(metainfo.author, metainfo.title)
            printEconbizOutput(res)
         #when there is no metadata available
         else:
            hits = []
            s = pdf_to_txt(mypath + '/' + f, 0, 0)
            paragraphs = re.split('\n+', s)
            end = findThreshold(5, len(paragraphs))
            for a in range(0, end):
               #search only if there are more than min_tokens words
               if len(paragraphs[a].split()) > min_tokens:
                  res = searchDataprovider("search", "title", paragraphs[a])
                  hit = selectBestMatch(paragraphs, res['hits']['hits'])
                  if hit != None:
                     bisect.insort_left(hits, hit)
            if len(hits) > 0:
               bestHit = hits[-1]
      except (AttributeError, TypeError, PdfReadError, IOError, AssertionError) as e:
         continue
   print(" done.")

   
def selectBestMatch(tokens, hits):
   results = []
   creatorWeight = 2
   titleWeight = 1
   for hit in hits:
      score = 0
      try:
         if hit.has_key('title'):
            foo = process.extractBests(hit['title'], tokens)
            if len(foo) > 0:
               score += foo[0][1] * titleWeight
         if hit.has_key('creator'):
            creatorScore = 0
            creators = hit['creator']
            for creator in creators:
               foo = process.extractBests(creator, tokens)
               if foo != None:
                  creatorScore += foo[0][1]
            if len(creators) > 0:
               score += (creatorScore/len(creators)) * creatorWeight
         bisect.insort_left(results, (score/(creatorWeight+titleWeight), hit))
      except UnicodeDecodeError as e:
         continue
   if len(results) > 0:
      return results[-1]
   return None

def findThreshold(max, objectLen):
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


def searchDataprovider(action="search", field="text", query=""):
   assert (action == "search" or action == "suggest")
   if action == "search":
      response = requests.get('https://api.econbiz.de/v1/search?q=' +field + ':' + query +'&echo=on')
   if action == "suggest":
      #response = requests.get('https://api.econbiz.de/v1/suggest/' + field + '/' + query + '&echo=on')
      response = requests.get('https://api.econbiz.de/v1/suggest/' + query + '&echo=on')
      
   if response.status_code == 200:
      return response.json()
   else:
      return None
   
if __name__ == "__main__":
   main()