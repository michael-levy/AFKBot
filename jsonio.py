import json

afkfile = open('./afks.json', 'r+')
afks = json.load(afkfile)

def write(key, value):
    afks[str(key)] = value
    afkfile.seek(0)
    json.dump(afks, afkfile, indent=4)

def remove(key):
    afks.pop(str(key))
    afkfile.seek(0)
    json.dump(afks, afkfile, indent=4)
    afkfile.truncate()

def read(key):
    return afks.get(str(key))

def contains(key):
    return str(key) in afks