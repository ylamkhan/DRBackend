import pickle

def serialize(obj):
    return pickle.dumps(obj)

def deserialize(blob):
    return pickle.loads(blob)
