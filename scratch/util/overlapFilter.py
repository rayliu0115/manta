#!/usr/bin/env python
#
# Manta
# Copyright (c) 2013-2014 Illumina, Inc.
#
# This software is provided under the terms and conditions of the
# Illumina Open Source Software License 1.
#
# You should have received a copy of the Illumina Open Source
# Software License 1 along with this program. If not, see
# <https://github.com/sequencing/licenses/>
#

"""
filter overlapping PASS SVs (except for BNDs)
"""

import os, sys
import re



def isInfoFlag(infoString,key) :
    word=infoString.split(";")
    for w in word :
        if w == key : return True
    return False

def getKeyVal(infoString,key) :
    match=re.search("%s=([^;\t]*);?" % (key) ,infoString)
    if match is None : return None
    return match.group(1);

class VCFID :
    CHROM = 0
    POS = 1
    REF = 3
    ALT = 4
    QUAL = 5
    FILTER = 6
    INFO = 7



class VcfRecord :
    def __init__(self, line) :
        self.line = line
        w=line.strip().split('\t')
        self.chrom=w[VCFID.CHROM]
        self.pos=int(w[VCFID.POS])
        self.qual=w[VCFID.QUAL]
        self.isPass=(w[VCFID.FILTER] == "PASS")
        self.Filter=w[VCFID.FILTER]
        self.endPos=self.pos+len(w[VCFID.REF])-1
        val = getKeyVal(w[VCFID.INFO],"END")
        if val is not None :
            self.endPos = int(val)
        val = getKeyVal(w[VCFID.INFO],"SOMATICSCORE")
        if val is not None :
            self.ss = int(val)
        else :
            self.ss = None
        self.svtype = getKeyVal(w[VCFID.INFO],"SVTYPE")
        self.isInv3 = isInfoFlag(w[VCFID.INFO],"INV3")
        self.isInv5 = isInfoFlag(w[VCFID.INFO],"INV5")



class Constants :

    import re

    contigpat = re.compile("^##contig=<ID=([^,>]*)[,>]")



def processStream(vcfFp, chromOrder, header, recList) :
    """
    read in a vcf stream
    """

    import re

    for line in vcfFp :
        if line[0] == "#" :
            header.append(line)
            match = re.match(Constants.contigpat,line)
            if match is not None :
                chromOrder.append(match.group(1))
        else :
            recList.append(VcfRecord(line))



def getOptions() :

    from optparse import OptionParser

    usage = "usage: %prog < vcf > sorted_unique_inv_vcf"
    parser = OptionParser(usage=usage)

    (options,args) = parser.parse_args()

    if len(args) != 0 :
        parser.print_help()
        sys.exit(2)

    return (options,args)



def resolveRec(recOverlapSet, recList) :
    """
    determine which of a set of overlapping vcf records to keep
    """

    if not recOverlapSet: return
    if len(recOverlapSet) == 1:
        recList.append(recOverlapSet[0])
        return

    # dead simple start, kick out the largest variant:

    largestSize=0
    largestIndex=0
    for (index,rec) in enumerate(recOverlapSet) :
        assert rec.pos > 0

        size=rec.endPos-rec.pos
        if size > largestSize :
            largestSize = size
            largestIndex = index

    for (index,rec) in enumerate(recOverlapSet) :
        if index == largestIndex : continue
        recList.append(rec)



def main() :

    outfp = sys.stdout

    (options,args) = getOptions()

    header=[]
    recList=[]
    chromOrder=[]

    processStream(sys.stdin, chromOrder, header, recList)

    def vcfRecSortKey(x) :
        """
        sort vcf records for final output

        Fancy chromosome sort rules:
        if contig records are found in the vcf header, then sort chroms in that order
        for any chrom names not found in the header, sort them in lex order after the
        found chrom names
        """

        try :
            headerOrder = chromOrder.index(x.chrom)
        except ValueError :
            headerOrder = size(chromOrder)

        return (headerOrder, x.chrom, x.pos, x.endPos)

    recList.sort(key = vcfRecSortKey)

    for line in header :
        outfp.write(line)

    recList2 = []
    recOverlapSet = []
    lastRec = None
    for vcfrec in recList :
        # shortcut directly to non-filtered set:
        if (not vcfrec.isPass) or (vcfrec.svtype == "BND") :
            recList2.append(vcfrec)
            continue

        rec = [vcfrec.chrom, vcfrec.pos, vcfrec.endPos]

        def isIntersect(rec1,rec2) :
            return (((rec1[1]+250) < rec2[2])  and ((rec1[2]-250) > rec2[1]))

        if ((lastRec is None) or
            (rec[0] != lastRec[0]) or
            (not isIntersect(rec,lastRec))) :
            resolveRec(recOverlapSet,recList2)
            recOverlapSet = []
            lastRec = None
   
        recOverlapSet.append(vcfrec)
        if lastRec is None :
            lastRec = rec
        else :
            lastRec[1] = min(rec[1],lastRec[1])
            lastRec[2] = max(rec[2],lastRec[2])

    resolveRec(recOverlapSet,recList2)

    recList = recList2
    recList.sort(key = vcfRecSortKey)

    for vcfrec in recList :
        outfp.write(vcfrec.line)


main()

