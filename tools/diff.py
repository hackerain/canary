# -*- coding: utf-8 -*-

INDEX1 = "index1.txt"
INDEX2 = "index2.txt"

index1 = set()
index2 = set()

print "reading index1"
with open(INDEX1) as f:
    for line in f:
        index1.add(line.strip())
print "reading index1 done"

print "reading index2"
with open(INDEX2) as f:
    for line in f:
        index2.add(line.strip())
print "reading index2 done"


def w(s, n):
    with open(n+".txt", "w") as f:
        for i in s:
            f.write(str(i)+"\n")


# 差集
def diff1():
    print "caculating difference 1"
    s = index1 - index2
    print "caculating difference 1 done"

    print "writing difference 1"
    w(s, 'index_diff1')
    print "writing difference 1 done"

# 差集
def diff2():
    print "caculating difference 2"
    s = index2 - index1
    print "caculating difference 2 done"

    print "writing difference 2"
    w(s, 'index_diff2')
    print "writing difference 2 done"


# 并集
def union():
    print "caculating union"
    s = index1 | index2
    print "caculating union done"
    
    print "writing union"
    w(s, 'index_union')
    print "writing union done"

# 交集
def intersection():
    print "caculating intersection"
    s = index1 & index2
    print "caculating intersection done"
    
    print "writing intersection"
    w(s, 'index_intersection')
    print "writing intersection done"


# 并集-交集，即没有重叠的元素
def symmetric():
    print "caculating symmetric"
    s = index1 ^ index2
    print "caculating symmetric done"
    
    print "writing symmetric"
    w(s, 'index_symmetric')
    print "writing symmetric done"


diff1()
diff2()
union()
intersection()
symmetric()
