import re

# For finding a rating about a user the bot returns
def find_float_or_int(string):
    match = re.search("[-+]?\d*\.\d+|\d+", string)
    if match:
        return float(match.group())
    else:
        return None
