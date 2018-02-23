import numpy as np

def LevenshteinMatrix(s,t):
    '''
    (list,list) -> matrix or (str, str) -> matrix
    Calculate the matrix distance between two strings s and t
    '''
    nrow = len(s) + 1
    ncol = len(t) + 1
    d = np.zeros([nrow,ncol])
    #initizalize array
    for i in range(nrow):
        d[i,0] = i
    for j in range(ncol):
        d[0,j] = j

    # fill out the array:
    subcost = 0
    for i in range(1,nrow):
        for j in range(1,ncol):
            if s[i-1] == t[j-1]:
                subcost = 0
            else:
                subcost = 1
            d[i][j] = min(d[i-1,j]+1, d[i,j-1]+1, d[i-1,j-1]+subcost)
    print(d)
    return d

def LevenshteinDistance(s,t):
    '''
    (list,list) -> int or (str, str) -> int
    Calculate the distance between two strings s and t
    Matrix implementation is used (DP)
    '''
    d = LevenshteinMatrix(s,t)
    return d[len(s),len(t)]


def getMatchMatrix(s,t):
    '''
    (list,list) -> matrix or (str, str) -> matrix
    Len(s) >> Len(t), return the matrix for fuzzy matching
    '''
    d = LevenshteinMatrix(s,t)
    nrow = len(s) + 1
    ncol = len(t) + 1
    assert(nrow > ncol), "SONGMATCH, getMatchMatrix: first string must be longer than the second string!"
    #normalizer = 1
    #for i in range(ncol,nrow):
    #    for j in range(ncol):
    #        d[i][j] = d[i][j] - d[i-nrow][j]
    #    normalizer += 1
    return d

def getMatchVal(s,t):
    '''
    (list,list) -> int or (str, str) -> int
    return the ending index of the best matching
    '''
    d = getMatchMatrix(s,t)
    nrow = len(s) + 1
    colind = len(t)
    minval = len(t)+1
    index = 0
    for i in range(1, nrow):
        if (d[i,colind] < minval):
            index = i
            minval = d[i,colind]
    return minval


class SongMatch:
    def __init__(self, s=''):
        self.s = s # song DB
        self.t = '' # matching word
        self.d = []
        self.transpositionCost = 1
        self.dropoutCost = 1
        self.duplicationCost = 1
        self._counter = 0
        self._activeColumn = 0
        self._inactiveColumn = 1
        self._modifySongFlag = True
        self._initizalized = False

    def modifySong(self,s):
        assert(self._modifySongFlag), "SONGMATCH, cannot modify song DB！"
        self.s = s

    def addNote(self,note):
        # note is a single character string
        assert(len(note) == 1), "SONGMATCH, addNote argument length is not 1!"
        self.t += note
        self._counter += 1
        nrow = len(self.s) + 1
        if (not self._initizalized):
            assert(self.s), "SONGMATCH, song DB string uninitialized"
            self.d = np.zeros([nrow, 2])
            for i in range(nrow):
                self.d[i,0] = i
            for j in range(2):
                self.d[0,j] = j
            self._initizalized = True
            self._modifySongFlag = False
            self._activeColumn = 0
            self._inactiveColumn = 1

        # swap active and inactive column
        tmp = self._activeColumn
        self._activeColumn = self._inactiveColumn
        self._inactiveColumn = tmp
        # initizalize the column value for the next iteration
        self.d[0,self._activeColumn] = self._counter
        for i in range(1,nrow):
            if self.s[i-1] == self.t[self._counter-1]:
                subcost = 0
            else:
                subcost = self.transpositionCost
            self.d[i][self._activeColumn] = min(self.d[i-1,self._activeColumn]+self.duplicationCost,
             self.d[i,self._inactiveColumn]+self.dropoutCost, self.d[i-1,self._inactiveColumn]+subcost)
        # print(self.d) # print out the columns
        return self.getMatchVal()

    def addNotes(self,notes):
        # return the match value for the last note
        assert(len(notes) > 0), "SONGMATCH, addNotes argument length is 0!"
        val = 0
        for i in notes:
            val = self.addNote(i)
        return val

    def getMatchVal(self):
        nrow = len(self.s) + 1
        minval = self._counter + 1
        index = 0
        for i in range(1, nrow):
            if (self.d[i,self._activeColumn] < minval):
                index = i
                minval = self.d[i,self._activeColumn]
        return minval




if __name__ == "__main__":
    out1 = LevenshteinDistance('sitting','kitten')
    print(out1)
    #out2 = LevenshteinDistance('Sunday','Saturday')
    #print(out2)
    #out3 = getMatchVal('abcdefghijklmnopqrstuvwxyz','opqr')
    #out4 = getMatchVal('sittingsttingkitt1en123sitting','kitten')
    #print(out3)
    #print(out4)

    test1 = SongMatch('sitting')
    print(test1.addNotes('kitten'))
