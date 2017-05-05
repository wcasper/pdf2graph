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

    if "setcolorspace" in block or "image" in block or "imagemask" in block:
      image = EPSImage()
      blen = len(block)

      for i in range(blen):
        val = block[i]
        if(val == "setcolorspace"):
          image.setup.values[11] = block[i-1]
        elif(val == "/ImageType"):
          image.setup.values[0] = block[i+1]
        elif(val == "/Width"):
          image.setup.values[1] = block[i+1]
        elif(val == "/Height"):
          image.setup.values[2] = block[i+1]
        elif(val == "/Interpolate"):
          image.setup.values[3] = block[i+1] == "true"  
        elif(val == "/BitsPerComponent"):
          image.setup.values[4] = block[i+1]
        elif(val == "/Decode"):
          if(block[i+1] == "["):
            tmp = []
            for j in range(i+2,blen):
              if(block[j] == "]"):
                break
              else:
                tmp.append(block[j])
            image.setup.values[5] = tmp
        elif(val == "/DataSource"):
          image.setup.values[6] = block[i+1]
        elif(val == "/ASCII85Decode"):
          image.setup.values[7] = block[i+1]
        elif(val == "/FlateDecode" or val == "/DCTDecode"):
          image.setup.values[8] = block[i]
          image.setup.values[9] = block[i+1]
        elif(val == "/ImageMatrix"):
          if(block[i+1] == "["):
            tmp = []
            for j in range(i+2,blen):
              if(block[j] == "]"):
                break
              else:
                tmp.append(block[j])
            image.setup.values[10] = tmp
        elif val == "image" or val == "imagemask":
          image.setup.values[12] = val
          end = i + 1
          if end < blen:
            while not (block[end].endswith('~>Q') or block[end].endswith('~>')):
              end += 1
            end = min(end+1,blen)
            image.encoded = block[i+1:end]

      objects.append(image)

    elif("c" in block or "l" in block or "re" in block):
      path = EPSVectorPath()
      blen = len(block)
      # affine transformation
      a = 1
      b = 0
      c = 0
      d = 1
      tx = 0
      ty = 0
      for i in range(blen):
        val = block[i]
        if(val == "cm"):
          # get the transformation matrix
          a = float(block[i-6])
          b = float(block[i-5])
          c = float(block[i-4])
          d = float(block[i-3])
          tx = float(block[i-2])
          ty = float(block[i-1])

        if(val == "c"):
          x0 = float(block[i-6])
          y0 = float(block[i-5])
          x = a*x0 + c*y0 + tx
          y = b*x0 + d*y0 + ty
          path.x.append(x)
          path.y.append(y)

          x0 = float(block[i-4])
          y0 = float(block[i-3])
          x = a*x0 + c*y0 + tx
          y = b*x0 + d*y0 + ty
          path.x.append(x)
          path.y.append(y)

          x0 = float(block[i-2])
          y0 = float(block[i-1])
          x = a*x0 + c*y0 + tx
          y = b*x0 + d*y0 + ty
          path.x.append(x)
          path.y.append(y)

          path.t.append("c")

        elif(val == "l"):
          x0 = float(block[i-2])
          y0 = float(block[i-1])
          x = a*x0 + c*y0 + tx
          y = b*x0 + d*y0 + ty
          path.x.append(x)
          path.y.append(y)

          path.t.append("l")

        elif(val == "m"):
#          # everytime we move, we "lift the pen"
#          # starting a new path
          if (len(path.x) > 0):
            path.n = len(path.x)
            objects.append(path.copy())
            path = EPSVectorPath()
            
          x0 = float(block[i-2])
          y0 = float(block[i-1])
          x = a*x0 + c*y0 + tx
          y = b*x0 + d*y0 + ty
          path.x.append(x)
          path.y.append(y)
          
          path.t.append("m")

        elif(val == "g"):
          path.color = (float(block[i-1]))
        elif(val == "f" or val == "f*"):
          path.filled = True
          path.completed = True
          path.x.append(path.x[0])
          path.y.append(path.y[0])
          path.t.append("l")
        elif(val == "h"):
          path.completed = True
          path.x.append(path.x[0])
          path.y.append(path.y[0])
          path.t.append("l")
        elif(val == "re"):
          x0 = float(block[i-4])
          y0 = float(block[i-3])
          dx0 = float(block[i-2])
          dy0 = float(block[i-1])
          x = a*x0 + c*y0 + tx
          y = b*x0 + d*y0 + ty
          dx = a*dx0 + c*dy0
          dy = b*dx0 + d*dy0
          path.x.append(x)
          path.y.append(y)
          path.t.append("l")
          path.x.append(x+dx)
          path.y.append(y)
          path.t.append("l")
          path.x.append(x+dx)
          path.y.append(y+dy)
          path.t.append("l")
          path.x.append(x)
          path.y.append(y+dy)
          path.t.append("l")
          path.x.append(x)
          path.y.append(y)
          path.t.append("l")
          path.completed = True

      path.n = len(path.x)
      if(path.n > 1):
        objects.append(path)

  return objects

