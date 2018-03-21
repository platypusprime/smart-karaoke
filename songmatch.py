import numpy as np
import math

DEBUG = 0

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
    if DEBUG:
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

class SongMatchNew:
    def __init__(self, songname = '', s=[], stime=[]):
        self.s = s # song DB
        self.stime = stime
        self.t = [] # matching word
        self.d = []
        self.songname = songname
        self.alpha = 0 # transpose fix cost
        self.beta = 1 # duplicate fix cost
        self.gamma = 1 # dropout fix cost
        self.diffmat = []
        self._counter = 0
        self._activeColumn = 0
        self._inactiveColumn = 1
        self._modifySongFlag = True
        self._initizalized = False

    def getstime(self):
        return self.stime

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
            for j in range(1): # only the first c is initialized
                self.d[0,j] = j
            for i in range(1, nrow):
                self.d[i,0] = self.d[i-1,0] + self.gamma + self.s[i-1]**2
            self._initizalized = True
            self._modifySongFlag = False
            self._activeColumn = 0
            self._inactiveColumn = 1

        # swap active and inactive column
        tmp = self._activeColumn
        self._activeColumn = self._inactiveColumn
        self._inactiveColumn = tmp
        # initizalize the column value for the next iteration
        self.d[0,self._activeColumn] = self.d[0,self._inactiveColumn] + self.beta + self.t[self._counter-1] ** 2
        for i in range(1,nrow):
            transpositionCost = self.d[i-1,self._inactiveColumn] + ((self.s[i-1] - self.t[self._counter-1]) ** 2 + self.alpha)
            duplicationCost = self.d[i,self._inactiveColumn] + ((self.t[self._counter-1]) ** 2 + self.beta)
            dropoutCost = self.d[i-1,self._activeColumn] + ((self.s[i-1]) ** 2 + self.gamma)
            # if self._counter > 1:
            #     duplicationCost = self.d[i,self._inactiveColumn] + ((self.t[self._counter-1] + self.t[self._counter-2]) ** 2 + self.beta)
            # else:
            #     duplicationCost = self.d[i,self._inactiveColumn] + ((self.t[self._counter-1] + 0) ** 2 + self.beta)
            # if i > 1:
            #     dropoutCost = self.d[i-1,self._activeColumn] + ((self.s[i-1] + self.s[i-2]) ** 2 + self.gamma)
            # else:
            #     dropoutCost = self.d[i-1,self._activeColumn] + ((self.s[i-1] + 0) ** 2 + self.gamma)
            self.d[i][self._activeColumn] = min(duplicationCost, dropoutCost, transpositionCost)
        if DEBUG:
            print(self.d) # print out the columns
        return self.getMatchVal(True)

    def addNotes(self,notes):
        # return the match value for the last note
        assert(len(notes) > 0), "SONGMATCH, addNotes argument length is 0!"
        val = 0
        for i in notes:
            val = self.addNote([i])
        return val

    def getMatchVal(self, update = False):
        nrow = len(self.s) + 1
        minval = 10000
        index = 0
        for i in range(1, nrow):
            if (self.d[i,self._activeColumn] <= minval):
                index = i
                minval = self.d[i,self._activeColumn]
        if update:
            # partial order matching
            self.diffmat.append([index,self._counter])
        return minval

    def getCountVal(self):
        return self._counter

    def getKeyTempo(self, sfkey, tfkey, ttime):
        skeyl = [sfkey]
        tkeyl = [tfkey]
        # reconstruct full key list
        assert(len(ttime) == self._counter + 1),"SongMatchNew:getKeyTempo timelist and counter mismatch"
        assert(len(self.diffmat) == self._counter), "SongMatchNew:getKeyTempo length of diffmat is wrong"
        n = len(self.diffmat)
        for i in range(0,n):
            tkeyl.append(tkeyl[i] + self.t[i])
        for i in range(0,len(self.s)):
            skeyl.append(skeyl[i] + self.s[i])
        # self.stime, ttime : tempo list
        # skeyl, tkeyl : key list
        if 1:
            print("skeyl and tkeyl vals:")
            print(skeyl)
            print(tkeyl)
            print("DIFFMAT: " + str(self.diffmat))
            print("stime and ttime:")
            print(self.stime)
            print(ttime)
        # key average algorithm:
        keydifftotal = tfkey - sfkey
        for i in self.diffmat:
            keydifftotal += tkeyl[i[1]] - skeyl[i[0]]
        keydiff = keydifftotal/(n+1)

        # tempo crude average algorithm:
        # temporatio = (ttime[self.diffmat[-1][1]] - ttime[0])/(self.stime[self.diffmat[-1][0]] - self.stime[0])
        temporatio = (self.stime[self.diffmat[-1][0]])/(ttime[self.diffmat[-1][1]])

        # where to play
        startpt = self.stime[self.diffmat[-1][0]+1]
        return [keydiff, temporatio, startpt]

class SongMatch:
    def __init__(self, songname = '', s=''):
        self.s = s # song DB
        self.t = '' # matching word
        self.d = []
        self.songname = songname
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
        if DEBUG:
            print(self.d) # print out the columns
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

    def getCountVal(self):
        return self._counter

class SongsMatch:
    def __init__(self, dic):
        self.songMatchDic = {}
        self.probDic = {}
        self.newprobDic = {}
        self.avgWeight = 0.3
        self.notDBCost = 1
        self._counter = 0
        self._SONGNOTINDBSTR = 'Others'
        initprob = 1.0/(len(dic)+1)
        for i in dic:
            # i is the name, dic[i] is s
            self.songMatchDic[i] = SongMatch(i,dic[i])
            self.probDic[i] = initprob
        self.probDic[self._SONGNOTINDBSTR] = initprob
        return

    def addNote(self, note):
        cost = {}
        totalsum = 0
        for i in self.songMatchDic:
            # negative cost is used
            cost[i] = self.songMatchDic[i].addNote(note)
            self._counter = self.songMatchDic[i].getCountVal()
            self.newprobDic[i] = math.exp(-cost[i])
            totalsum += self.newprobDic[i]
        # update NOTINDB case
        self.newprobDic[self._SONGNOTINDBSTR] = math.exp(- self._counter * self.notDBCost)
        totalsum += self.newprobDic[self._SONGNOTINDBSTR]

        for i in self.newprobDic:
            self.probDic[i] = self.avgWeight * self.probDic[i] + (1-self.avgWeight) * self.newprobDic[i]/totalsum
        return cost

    def addNotes(self,notes):
        # return the match value for the last note
        assert(len(notes) > 0), "SONGSMATCH, addNotes argument length is 0!"
        cost = {}
        for j in notes:
            cost = self.addNote(j)
        return cost

    def getProbDic(self):
        '''
        return the dictionary of probability
        '''
        return self.probDic

class SongsMatchNew:
    def __init__(self, dic, timedic={}):
        self.songMatchDic = {}
        self.probDic = {}
        self.newprobDic = {}
        self.avgWeight = 0.5
        self.notDBCost = 3
        self._counter = 0
        self._SONGNOTINDBSTR = 'Others'
        initprob = 1.0/(len(dic)+1)
        for i in dic:
            # i is the name, dic[i] is s
            if i not in timedic:
                self.songMatchDic[i] = SongMatchNew(i,dic[i])
            else:
                self.songMatchDic[i] = SongMatchNew(i,dic[i],timedic[i])
            self.probDic[i] = initprob
        self.probDic[self._SONGNOTINDBSTR] = initprob
        return

    def addNote(self, note):
        cost = {}
        totalsum = 0
        for i in self.songMatchDic:
            # negative cost is used
            cost[i] = self.songMatchDic[i].addNote(note)
            self._counter = self.songMatchDic[i].getCountVal()
            self.newprobDic[i] = math.exp(-cost[i])
            totalsum += self.newprobDic[i]
        # update NOTINDB case
        self.newprobDic[self._SONGNOTINDBSTR] = math.exp(- self._counter * self.notDBCost)
        totalsum += self.newprobDic[self._SONGNOTINDBSTR]

        for i in self.newprobDic:
            self.probDic[i] = self.avgWeight * self.probDic[i] + (1-self.avgWeight) * self.newprobDic[i]/totalsum
        return cost

    def addNotes(self,notes):
        # return the match value for the last note
        assert(len(notes) > 0), "SONGSMATCH, addNotes argument length is 0!"
        cost = {}
        for j in notes:
            cost = self.addNote([j])
        return cost

    def getProbDic(self):
        '''
        return the dictionary of probability
        '''
        return self.probDic

    def getKeyTempo(self, songname, sfkey, tfkey, ttime):
        assert(songname in self.songMatchDic), "SONGSMATCHNEW, getKeyTempo invalid song name"
        return self.songMatchDic[songname].getKeyTempo(sfkey, tfkey, ttime)




if __name__ == "__main__":
    out1 = LevenshteinDistance('sitting','kitten')
    print(out1)

    # test1 = SongsMatch({'test1':'sitting'})
    # print(test1.addNotes('kitten'))
    # print(test1.getProbDic())
    DEBUG = 0
    print("------test1------")
    test1 = SongsMatchNew({'test1':[1,2,3]})
    print(test1.addNotes([1,1,3]))
    print(test1.getProbDic())
    print(test1.songMatchDic['test1'].diffmat)
    print("------test2------")
    test2 = SongsMatchNew({'test2':[1,1,1]},{'test2':[0,1,2,3]})
    print(test2.addNotes([0,0,0]))
    print(test2.getProbDic())
    print(test2.songMatchDic['test2'].diffmat)
    print(test2.getKeyTempo('test2',12,12,[1,2,5,7]))
