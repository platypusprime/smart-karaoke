# -*- coding: utf-8 -*-
"""
Created on Tue Apr 17 17:26:08 2018

@author: damichoi
"""
# step1
a = [0.5,1,1,1,0.5,0.5,0.5,0.5,0.5,1.5,0.5,0.5,0.5,2,0.5,0.5,4,0.5,0.5,0.5,0.5,1.5,0.5,0.5,3,0.5,0.5,0.5,2,0.5,0.5,5.5,0.5,1,1,1,1,1,1,1,1,1,1,0.5,4]
# step2
b = []
acc = 0
for i in a:
    acc += i
    b.append(acc)
    
print(b)
# step3
bpm = 138

time = 60/bpm
c = []
for i in b:
    c.append(i*time)
print(c)
# step 4
offset = 31.5*time
d = []
for i in c:
    d.append(i+offset)
print(d)
