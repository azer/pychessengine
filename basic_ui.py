"""
Basic Test Interface for Chess Engine <http://pychessengine.googlecode.com>
Azer Koculu <http://azer.kodfabrik.com>
v1.0: 11 Nov 2008~23 Nov 2008 01:19
v1.1: 16 Dec 2008 09:08 
"""

VERSION = '1.1'
AUTHOR = 'Azer Koculu <http://azer.kodfabrik.com>'
COPYRIGHT = 'Copyright (C) 2008 Azer Koculu'
LICENSE = 'GPL'

from chessengine import Board
from pieceset import default as defaultset
from re import match
from sys import exc_info

board = None
color = ("White","Black")
coordinate = r"[a-h][1-8]"
symbol = (None,"P","N","B","R","Q","K")

def cmd(uinput):
  args = uinput.split(" ")
  command = args[0]
  
  if command == "move":
    if match(coordinate,args[1]) and match(coordinate,args[2]):
      piece = board.square[ ord(args[1][0])-97 ][ int(args[1][1])-1 ].piece
      if piece and piece.symbol[0]==board.next:
        square = board.square[ ord(args[2][0])-97 ][ int(args[2][1])-1 ]
        if piece.movement.count(square):
          if piece.symbol[1] == 6 and abs(piece.square.x-square.x)==2:
            rook = board.square[piece.square.x+( piece.square.x<square.x and 3 or -4 )][piece.square.y].piece
            rook.move( board.square[piece.square.x+( piece.square.x<square.x and 1 or -1 )][piece.square.y] )
        
          piece.move( square )
          board.next = int(not piece.symbol[0])
          show()
        else:
          raise Exception,"Invalid move."
      else: 
        raise Exception,"Given coordinate doesn't contain any %s piece."%color[board.next]
    else:
      raise Exception,"Invalid input."
  elif command == "threat":
    if match(coordinate,args[1]):
      square = board.square[ ord(args[1][0])-97 ][ int(args[1][1])-1 ]
      print ",".join([ "%s%i"%(chr(piece.square.x+97),piece.square.y+1) for piece in square.threat ])
    else:
      raise Exception,"Invalid input."
  elif command == "test":
    if match(coordinate,args[1]):
      piece = board.square[ ord(args[1][0])-97 ][ int(args[1][1])-1 ].piece
      print ",".join([ "%s%i"%(chr(square.x+97),square.y+1) for square in piece.movement ])
    else:
      raise Exception,"Invalid input."
  elif command == "show":
    show()
  elif command == "info":
    print "# pyChessEngine\n# VERSION: %s\n# AUTHOR: %s"%(VERSION,AUTHOR)
  elif command == "quit":
    return False
  elif command == "help":
    print """
move        Moves pieces.                       move a2 a3
show        Shows the board.                    show
test        Sorts legal moves for pieces        test b1
threat      Sorts threats for squares           threat e5
info
quit
help
    """
  else:
    raise Exception,"Unknown command."
  return True
  
def getInput():
  ok = True
  while ok:
    try:
      cmd(raw_input("%s> "%color[ board.next ]))
    except:
      print "ERROR: %s"%exc_info()[1]
  
def getPieceName(piece):
  return not piece.symbol[0] and symbol[ piece.symbol[1] ] or symbol[ piece.symbol[1] ].lower()

def main():
  show()
  getInput()
  
def show():
  rstart,rend,rstep = board.next and (0,8,1) or (7,-1,-1)
  print ". . %(colname)s . .\n+ ------------------- +\n%(data)s \n+ ------------------- +\n. . %(colname)s . ."%{
    "data":"\n".join([ "%(i)i | %(square)s | %(i)i"%{ "i":(y+1), "square":" ".join([ board.square[x][y].piece and getPieceName(board.square[x][y].piece) or "." for x in range(8) ]) } for y in range(rstart,rend,rstep) ]),
    "colname": " ".join([ chr(i) for i in xrange(97,105) ])
  }

if __name__ == "__main__":
  board = Board(defaultset)
  main()
