#!/usr/bin/python

##
# This is a script for interpreting the vector output of an EPS file
##

from epsclass import *

def get_eps_objects(content):
  objects = []

  values = content.split()

  nval = len(values)

  # partition the input values into blocks
  blocks = [i for i,x in enumerate(values) if x == "q" or x == "Q" ]
  nblocks = len(blocks)

  # inside each block, try to identify an object
  for ib in range(nblocks):
    b1 = blocks[ib]
    b0 = blocks[ib-1]
    block = values[b0:b1]

    print(block)

    if "setcolorspace" in block:
      image = EPSImage()
      blen = len(block)

      for i in range(blen):
        val = block[i]
        if(val == "/ImageType"):
          image.setup.values[0] = int(block[i+1])
        elif(val == "/Width"):
          image.setup.values[1] = int(block[i+1])
        elif(val == "/Height"):
          image.setup.values[2] = int(block[i+1])
        elif(val == "/Interpolate"):
          if(block[i+1] == "false"):
            image.setup.values[3] = False
          else:
            image.setup.values[3] = False
        elif(val == "/BitsPerComponent"):
          image.setup.values[4] = int(block[i+1])
        elif(val == "/Decode"):
          if(block[i+1] == "["):
            tmp = []
            for j in range(i+2,blen):
              if(block[j] == "]"):
                break
              else:
                tmp.append(int(block[j]))
            image.setup.values[5] = tmp
        elif(val == "/DataSource"):
          image.setup.values[6] = block[i+1]
        elif(val == "/ASCII85Decode"):
          image.setup.values[7] = block[i+1]
        elif(val == "/FlateDecode"):
          image.setup.values[8] = block[i+1]
        elif(val == "/ImageMatrix"):
          if(block[i+1] == "["):
            tmp = []
            for j in range(i+2,blen):
              if(block[j] == "]"):
                break
              else:
                tmp.append(int(block[j]))
            image.setup.values[9] = tmp

        elif(val == "imagemask"):
          image.imagemask = block[i+1]


      objects.append(image)

    elif("c" in block or "l" in block):
      path = EPSVectorPath()
      blen = len(block)
      for i in range(blen):
        val = block[i]
        if(val == "c"):
          path.x.append(float(block[i-6]))
          path.x.append(float(block[i-4]))
          path.x.append(float(block[i-2]))
          path.y.append(float(block[i-5]))
          path.y.append(float(block[i-3]))
          path.y.append(float(block[i-1]))
          path.t.append("c")
        elif(val == "l"):
          path.x.append(float(block[i-2]))
          path.y.append(float(block[i-1]))
          path.t.append("l")
        elif(val == "m"):
          path.x.append(float(block[i-2]))
          path.y.append(float(block[i-1]))
          path.t.append("m")
        elif(val == "g"):
          path.color = float(block[i-1])
        elif(val == "f" or val == "f*"):
          path.filled = True
        elif(val == "f*" or val == "h"):
          path.completed = True

      path.n = len(path.x)
      objects.append(path)

  return objects

