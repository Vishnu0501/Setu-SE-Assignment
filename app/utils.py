from decimal import Decimal

def serialize(obj):
    if isinstance(obj,list):
        return [serialize(i) for i in obj]
    if hasattr(obj,"items"):
        return {k: serialize(v) for k, v in obj.items()}
    if isinstance(obj, Decimal):
        return float(obj)
    return obj