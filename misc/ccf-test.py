from binascii import hexlify, unhexlify

def mask(n):
   """Return a bitmask of length n (suitable for masking against an
      int to coerce the size to a given length)
   """
   if n >= 0:
       return 2**n - 1
   else:
       return 0
 
def rol(n, rotations=1, width=8):
    """Return a given number of bitwise left rotations of an integer n,
       for a given bit field width.
    """
    rotations %= width
    if rotations < 1:
        return n
    n &= mask(width) ## Should it be an error to truncate here?
    return ((n << rotations) & mask(width)) | (n >> (width - rotations))
 
def ror(n, rotations=1, width=8):
    """Return a given number of bitwise right rotations of an integer n,
       for a given bit field width.
    """
    rotations %= width
    if rotations < 1:
        return n
    n &= mask(width)
    return (n >> rotations) | ((n << (width - rotations)) & mask(width))
    
def pprint(matrix):
    
    if isinstance(matrix[0], int):
        x = [hex(i)[2:].upper().zfill(2) for i in matrix]
    else:
        x = [hexlify(matrix[i:i+1]).upper() for i in range(0, 64)]
    for row in [x[i:i+8] for i in range(0, 64, 8)]:
        print ' '.join(row)
    print

ccf = open('../test/test.ccf').read()

header = ccf[:12]
magic = int('0x'+ccf[12:20], 16)
padding =  64 - int('0x' + ccf[20:22], 16)
data = ccf[22:-padding*2]
raw = unhexlify(ccf[22:])

raw = unhexlify(ccf[22:22+128])
pprint(raw)
matrix = [int('0x'+hexlify(x), 16) for x in raw]

for i in range(64):
    if magic & 1 != 0:
        magic = ror(magic, magic & 0xff, 12)
    else:
        magic = rol(magic, magic & 0xff, 9)
    
    matrix[i] = matrix[i] ^ (magic & 0xff)
    
pprint(matrix)

matrix = list(sum(zip(*[matrix[i:i+8] for i in range(0, 64, 8)]), ())) # transposition

pprint(matrix)

for j in range(8):
    x = [matrix[(j*8) + k] for k in range(8)]
    for m in range(8):
        x[m] = x[m] ^ (magic & 0xff)
        
        print x
        x = sum([[int(i) for i in tuple(bin(b)[2:].zfill(8))] for b in x], [])
        x = list(sum(zip(*[x[i:i+8] for i in range(0, 64, 8)]), ()))
        
        if magic & 1 != 0:
            magic = ror(magic, magic & 12)
        else:
            magic = rol(magic, magic & 9)
    
    for n in range(8):
        matrix[(j*8) + n] = matrix[n]
        
pprint(matrix)