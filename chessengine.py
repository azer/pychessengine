"""
Chess Engine
Azer Koculu <http://azer.kodfabrik.com>
11 Nov 2008~23 Nov 2008 01:19
"""

VERSION = '1.0'
AUTHOR = 'Azer Koculu <http://azer.kodfabrik.com>'
COPYRIGHT = 'Copyright (C) 2008 Azer Koculu'
LICENSE = 'GPL'

import sys
import logging
from pdb import set_trace
from time import time
from sys import exc_info
from copy import copy

"""
logging.basicConfig(
  level = logging.DEBUG,
  format = "%(asctime)s %(levelname)s %(message)s",
  filename = 'log',
  filemode = 'w'
)
"""


white, black = range(0,2)
pawn, knight, bishop, rook, queen, king = range(1,7)

class Board(object):
  def __init__(self,data):
    self.__piece = []
    self.__time = 0
    self.isInitialized = False
    self.king = []
    self.square = []
    self.next = 0
    self.winner = -1
   
    for x in range(0,8):
      self.square.append([])
      for y in range(0,8):
        self.square[x].append( Square(self,x,y) )
    
    for piece in data:
      obj = Piece(board=self,square=self.square[piece["x"]][piece["y"]],symbol=( piece["color"], piece["value"] ),pid=piece.has_key("id") and piece["id"] or 0,is_moved=piece.has_key("is_moved") and piece["is_moved"] or False)
      logging.info("Board: Piece %ix%i was created."%(obj.square.x,obj.square.y))
      if obj.symbol[1] == 6:
        self.king.append(obj)
      self.piece.append(obj)
    
    self.isInitialized = True
    
    for piece in self.piece:
      if piece.symbol[1] < 6:
        piece.update()
        
    for king in self.king:
      king.update()

  def setTime(self,value):
    logging.info("Board: Setting time to %i "%value)
    self.__time = value
  
  def getTime(self):
    return self.__time
  
  def getPiece(self):
    #logging.info("Board (%i): %s"%(len(self.__piece),",".join([ "%ix%i"%(piece.square.x,piece.square.y) for piece in self.__piece ])))
    return self.__piece
    
  time = property(getTime,setTime)
  piece = property(getPiece)
  AxisTest = staticmethod(lambda x1,y1,x2,y2,linear,across: ( linear and ( x1==x2 or y1==y2 ) ) or ( across and ( abs(x1-x2)==abs(y1-y2) ) ))
  
  def MultiAxisTest(*args):
    coor = args[:-2]
    linear = args[-2:-1][0]
    across = args[-1]

    logging.info("Multi Axis Test: %s linear? %s across? %s"%( str(coor), str(linear), str(across) ))

    for i in range((len(coor)/2)-1):
      for t in range(len(coor)/2):
        if i==t:
          continue

        x1 = coor[i*2]
        y1 = coor[i*2+1]
        x2 = coor[t*2]
        y2 = coor[t*2+1]

        if not ( (linear and (x1==x2 or y1==y2) ) or ( across and abs(x1-x2)==abs(y1-y2) ) ):
          return False
          
    return True
  
  MultiAxisTest = staticmethod(MultiAxisTest)
  
class Piece:

  def __init__(self,board,symbol,square,pid,is_moved):
    self.board = board
    self.history = []
    self.is_moved = is_moved
    self.movement = []
    self.pid = pid
    self.relation = []
    self.symbol = symbol
    self.shield = []
    self.square = None
    self.threat = []
    self.time = 0
    
    self.move(square)
    
  def addShield(self,shield,threat,linear,across):
    logging.info("Piece %ix%i: piece-%ix%i is will be added as shield to piece-%ix%i"%(self.square.x,self.square.y,shield.square.x,shield.square.y,threat.square.x,threat.square.y))
    movement = shield.movement
    shield.movement = []
    
    for move in movement:
      if Board.MultiAxisTest(
        threat.square.x, threat.square.y,
        shield.square.x, shield.square.y,
        move.x, move.y,
        linear,
        across
      ):
        move.addMove(shield)
          
  def cleanShield(self):
    logging.info("Piece %ix%i: Cleaning shields... (%s)"%(self.square.x,self.square.y,",".join([ "%ix%i"%(piece.square.x,piece.square.y) for piece in self.shield ])))
    for shield in self.shield:
      logging.info("Piece %ix%i: shield-%ix%i gonna be updated."%(self.square.x,self.square.y,shield.square.x,shield.square.y))
      shield.update()
    self.shield = []
  
  def cleanRelation(self):
    logging.info("Piece %ix%i: Cleaning relations.."%(self.square.x,self.square.y))
    for square in self.relation:
      square.removeListener(self)
      if square.move.count(self): square.removeMove(self)
      if square.threat.count(self): square.removeThreat(self)
    self.movement, self.relation, self.threat = [],[],[]
  
  def createRange(self,horCoefficient,verCoefficient):
    logging.info("Piece %ix%i: Creating coordinate range.. coefficients: %ix%i"%(self.square.x,self.square.y,horCoefficient,verCoefficient))
    for i in range(1,9):
      x,y = self.square.x+( i*horCoefficient ),self.square.y+( i*verCoefficient )
      logging.info("Piece %ix%i: coordinate-%ix%i will be tried."%(self.square.x,self.square.y,x,y))
      if -1<x<8 and -1<y<8:
        logging.info("Piece %ix%i: square-%ix%i gonna be got the piece as threat and listener."%(self.square.x,self.square.y,x,y))
        square = self.board.square[x][y]
        square.addListener(self)
        square.addThreat(self)
        
        if square.isAvailableTo(self):
          logging.info("Piece %ix%i: as move too."%(self.square.x,self.square.y))
          square.addMove(self)
        
        if square.piece:
          logging.info("Piece %ix%i: Range gonna be broken at square-%ix%i which filled by piece-%i*%i."%(self.square.x,self.square.y,x,y,square.piece.symbol[0],square.piece.symbol[1]))
          break
      else:
        break
        
    logging.info("Piece %ix%i: coordinate range was created."%(self.square.x,self.square.y))

  def move(self,square):
    logging.info("Piece %ix%i: Moving to %ix%i.."%((self.square or square).x,(self.square or square).y,square.x,square.y))
    self.board.time = int(time()*10000)
    oldSquare = self.square
    square.setPiece(self)
    self.square.refresh(self)
    
    if oldSquare:
      self.is_moved = True
      oldSquare.piece = None
      oldSquare.refresh()
    self.update()
    
    for i in xrange(len(self.board.king)):
      self.board.king[i].update()
    
  def remove(self):
   logging.info("Piece %ix%i: Will be removed.."%(self.square.x,self.square.y))
   self.cleanRelation()
   self.square = None
   logging.info("Piece-%i,%i: Removed."%self.symbol)
   
  def update(self):

    if not self.board.isInitialized or self.board.time<=self.time:
      logging.info("Piece %ix%i: Board isn't initialized yet  or the piece is already updated. Board time: %i Self time: %i"%(self.square.x,self.square.y,self.board.time,self.time))
      return
    
    self.cleanRelation()
    
    x = self.square.x
    y = self.square.y
    dir = self.symbol[0] == white and 1 or -1

    if pawn == self.symbol[1]:
      isntMoved = y == (self.symbol[0] == white and 1 or 6)
      if ( y+dir>-1 and y+dir<8 ):
        square1 = self.board.square[x][y+dir]
        square1.addListener(self)
        
        if not square1.piece:
          square1.addMove(self)
          
          if isntMoved and ( y+(dir*2)>0 and y+(dir*2)<8 ):
            square2 = self.board.square[x][y+(dir*2)]
            square2.addListener(self)
            
            if not square2.piece:
              square2.addMove(self)
      
        if x-1>-1:
          square3 = self.board.square[x-1][y+dir]
          square3.addListener(self)
          square3.addThreat(self)
          
          if square3.piece and square3.piece.symbol[0] != self.symbol[0]:
            square3.addMove(self)
          
        if x+1<8:
          square4 = self.board.square[x+1][y+dir]
          square4.addListener(self)
          square4.addThreat(self)
          
          if square4.piece and square4.piece.symbol[0] != self.symbol[0]:
            square4.addMove(self)
            
    elif knight == self.symbol[1]:
      coor = [
        [x+1,y-2],
        [x+1,y+2],
        [x+2,y+1],
        [x+2,y-1],
        [x-1,y-2],
        [x-1,y+2],
        [x-2,y+1],
        [x-2,y-1]
      ]
        
      for c in coor:
        if -1<c[0]<8 and -1<c[1]<8:
          square = self.board.square[c[0]][c[1]]
          square.addListener(self)
          square.addThreat(self)
            
          if square.isAvailableTo(self):
            square.addMove(self)
            
    elif bishop == self.symbol[1]:
      self.createRange(1,1)
      self.createRange(-1,-1)
      self.createRange(1,-1)
      self.createRange(-1,1)
      
    elif rook == self.symbol[1]:
      self.createRange(1,0)
      self.createRange(-1,0)
      self.createRange(0,1)
      self.createRange(0,-1)
    
    elif queen == self.symbol[1]:
      self.createRange(1,1)
      self.createRange(-1,-1)
      self.createRange(1,-1)
      self.createRange(-1,1)
      self.createRange(1,0)
      self.createRange(-1,0)
      self.createRange(0,1)
      self.createRange(0,-1)
    
    elif king == self.symbol[1]:
      coor, threat = [
        [x+1,y-1],
        [x+1,y+1],
        [x+1,y],
        [x,y-1],
        [x,y+1],
        [x-1,y+1],
        [x-1,y],
        [x-1,y-1]
      ],None
      
      for i in xrange(len( self.square.threat )):
        tp = self.square.threat[i] # piece threat to the king
        if tp.symbol[0] != self.symbol[0]:
          #if threat:
          #  return self.board.close( self.symbol[0] or 0 )
          logging.info("Piece %ix%i: has got a threat named piece-%ix%i"%(self.square.x,self.square.y,tp.square.x,tp.square.y))
          threat = tp
      
      for i in xrange(8):
        c = coor[i]
        if -1<c[0]<8 and -1<c[1]<8:
          square = self.board.square[ c[0] ][ c[1] ]
          square.addListener(self)
          square.addThreat(self)
          if square.isAvailableTo(self):
            hasThreat = False
            
            logging.info("Piece %ix%i: Checking if square %ix%i has got threat or not."%(self.square.x,self.square.y,square.x,square.y))
            logging.info("Piece %ix%i: Threat data; %s"%(self.square.x,self.square.y,str([ "%ix%i"%(piece.square.x,piece.square.y) for piece in square.threat ])))
            for t in xrange(len(square.threat)):
              tp = square.threat[t] # piece threat to the square
              if tp.symbol[0]!=self.symbol[0]:
                hasThreat = True
                break
            
            if not hasThreat and threat and not threat.square == square:
                isLinear = self.square.isLinearTo(threat.square)
                logging.info("Piece %ix%i: Axis threat test: threat-%ix%i <> square-%ix%i"%(self.square.x,self.square.y,threat.square.x,threat.square.y,square.x,square.y))
                hasThreat = Board.AxisTest( threat.square.x, threat.square.y, square.x, square.y, isLinear and (threat.symbol[1]==4 or threat.symbol[1]==5), (not isLinear) and (threat.symbol[1]==3 or threat.symbol[1]==5) )
                logging.info("Piece %ix%i: islinear;%s hasthreat;%s "%(self.square.x,self.square.y,str(isLinear),str(hasThreat)))
            
            if not hasThreat:
              square.addMove(self)
      
      logging.info("Piece %ix%i: Checking castling."%(self.square.x,self.square.y))
   
      try:
        if self.board.isInitialized and len(self.history)==1 and not threat:
          if(
            not self.board.square[ x+1 ][y].piece and 
            not self.board.square[x+2][y].piece and 
            self.board.square[x+3][y].piece and
            self.board.square[x+3][y].piece.symbol[1] == 4 and
            len(self.board.square[x+3][y].piece.history)==1 and
            not self.board.square[x+3][y].piece.is_moved and
            not self.board.square[x+2][y].hasThreatTo(self) and
            not self.board.square[x+1][y].hasThreatTo(self)
          ):
            self.board.square[x+2][y].addMove(self)
              
          if (
              not self.board.square[ x-1 ][y].piece and 
              not self.board.square[x-2][y].piece and 
              not self.board.square[x-3][y].piece and 
              self.board.square[x-4][y].piece and
              self.board.square[x-4][y].piece.symbol[1] == 4 and
              len(self.board.square[x-4][y].piece.history)==1 and
              not self.board.square[x-4][y].piece.is_moved and
              not self.board.square[x-3][y].hasThreatTo(self) and
              not self.board.square[x-2][y].hasThreatTo(self) and
              not self.board.square[x-1][y].hasThreatTo(self)
          ):
            logging.info("Piece %ix%i: can left rook."%(self.square.x,self.square.y))
            self.board.square[x-2][y].addMove(self)
              
      except:
        logging.error(exc_info()[1])

      self.cleanShield()
      horAxisCoefficient,verAxisCoefficient = [1,1,0,-1,-1,-1, 0, 1],[0,1,1, 1, 0,-1,-1,-1]
      
      for i in xrange(0,8):
        shield = None
        for t in xrange(1,9):
          sx = x+(t*horAxisCoefficient[i])
          sy = y+(t*verAxisCoefficient[i])
          if -1<sx<8 and -1<sy<8:
            square = self.board.square[sx][sy]
            
            if square.piece and square.piece.symbol[1]<6:
              logging.info("Piece %ix%i: Checking Square %ix%i to move eleminating."%(self.square.x,self.square.y,sx,sy))
              if not shield and square.piece.symbol[0]!=self.symbol[0]:
                logging.info("Piece %ix%i: Piece %ix%i is an enemy shield."%(self.square.x,self.square.y,sx,sy))
                break
              elif not shield and square.piece.symbol[0] == self.symbol[0]:
                logging.info("Piece %ix%i: Piece %ix%i is a shield."%(self.square.x,self.square.y,sx,sy))
                shield = square.piece
              elif not shield and square.piece.symbol[0] == self.symbol[0]:
                logging.info("Piece %ix%i: Piece %ix%i is a double shield."%(self.square.x,self.square.y,sx,sy))
                break
              elif shield and square.piece.symbol[0] != self.symbol[0] and (
                ( abs( horAxisCoefficient[i] )!=abs( verAxisCoefficient[i] ) and 3<square.piece.symbol[1]<6 )
                or
                (  abs( horAxisCoefficient[i] )==abs( verAxisCoefficient[i] ) and ( square.piece.symbol[1] == 3 or square.piece.symbol[1]==5 ) )
              ):
                isLinear = self.square.isLinearTo( shield.square )
                self.addShield( shield, square.piece, isLinear, not isLinear )
          else:
            break
          
      if threat:
        logging.info("Piece %ix%i: Removing unshield moves."%(self.square.x,self.square.y))
        #logging.info("Board (%i): %s"%(len(self.board.piece),",".join([ "%ix%i"%(piece.square.x,piece.square.y) for piece in self.board.piece ])))
        shield = 0
        for piece in self.board.piece:
          if piece.square and piece.symbol[0] == self.symbol[0] and piece.square and piece.symbol[1]<6:
            self.shield.append( piece )
            logging.info("Piece %ix%i: Checking movement of %ix%i to remove unshield moves.."%(self.square.x,self.square.y,piece.square.x,piece.square.y))
            move = copy(piece.movement)
            
            if piece.symbol[1] == 1:
              for square in piece.threat:
                if square.piece and square.piece.symbol[0]!=square.piece.symbol[1]:
                  move.append(square)
            
            logging.info("Piece %ix%i: Diving into temporary move(%i) loop; %s"%(self.square.x,self.square.y,len(piece.movement)," ".join([ "%ix%i"%(sq.x,sq.y) for sq in move ])))
            
            piece.movement = []

            for s in range(len(move)):
              square = move[s]
              logging.info("Piece %ix%i: Square %ix%i, Threat %ix%i"%(self.square.x,self.square.y,square.x,square.y,threat.square.x,threat.square.y))
              
              if move.index(square)<s:
                logging.info("Piece %ix%i: Square %ix%i is already checked."%(self.square.x,self.square.y,square.x,square.y))
                continue
   
              isLinear = threat.square.isLinearTo( self.square )
              
              logging.info("Piece %ix%i: Linear threat? %s"%(self.square.x,self.square.y,str(isLinear)))
              logging.info("Piece %ix%i: Linear logic? %s"%(self.square.x,self.square.y,str(( isLinear and ( ( square.x==threat.square.x and square.x==x and square.y>min(threat.square.y,y) and square.y<max( threat.square.y, y ) ) or ( square.y==threat.square.y and square.y==y and square.x>min(threat.square.x,x) and square.x<max( threat.square.x, x ) ) ) ))))
              logging.info("Piece %ix%i: Across logic? %s"%(self.square.x,self.square.y,str(( not isLinear and ( ( square.x>min(threat.square.x,x) and square.x<max(threat.square.x,x) ) ) ))))
              logging.info("Piece %ix%i: Axis threat result? %s"%(self.square.x,self.square.y,str(Board.MultiAxisTest(x,y,threat.square.x,threat.square.y,square.y,square.x,isLinear,not isLinear))))
              
              if square==threat.square or (
                    threat.symbol[1]>2 and
                    (
                      ( isLinear and ( ( square.x==threat.square.x and square.x==x and square.y>min(threat.square.y,y) and square.y<max( threat.square.y, y ) ) or ( square.y==threat.square.y and square.y==y and square.x>min(threat.square.x,x) and square.x<max( threat.square.x, x ) ) ) )
                      or 
                      ( not isLinear and ( ( square.x>min(threat.square.x,x) and square.x<max(threat.square.x,x) ) ) )
                    ) and Board.MultiAxisTest(x,y,threat.square.x,threat.square.y,square.x,square.y,isLinear,not isLinear)
                  ):
   
                  piece.movement.append(square)
                  shield+=1

        if shield == 0 and len(self.movement)==0:
          self.board.winner = int(not self.symbol[0])
          
    self.time = int(time()*10000)

    
class Square:
  def __init__(self,board,x=0,y=0):
    self.x = x
    self.y = y
    self.board = board
    self.listener = []
    self.threat = []
    self.move = []
    self.piece = None
    self.time = 0
  
  isLinearTo = lambda self,square: self.x==square.x or self.y==square.y
  
  def hasThreatTo(self,piece):
    color = piece.symbol[0]
    for tpiece in self.threat:
      if tpiece.symbol[0] != piece.symbol[0]:
        return True
    return False
    
  def refresh(self,skip=None):
    logging.info("Square %ix%i: Refreshing.."%(self.x,self.y))
    listener = self.listener
    if self.board.time>self.time:
      logging.info("Square %ix%i: Cleaning relations."%(self.x,self.y))
      self.listener = []
      self.move = []
      self.threat = []
      self.time = int(time()*10000)
    
    for piece in listener:
      if piece!=skip and piece.symbol[1]!=6:
        piece.update()
  
  def isAvailableTo(self,piece):
    return not self.piece or self.piece.symbol[0] != piece.symbol[0]
  
  def addListener(self,piece):
    logging.info("Square %ix%i: Adding %ix%i as listener."%(self.x,self.y,piece.square.x,piece.square.y))
    logging.info("Square %ix%i: Listener data; %s"%(self.x,self.y,str(['%ix%i'%(p.square.x,p.square.y) for p in self.listener])))
    if piece.relation.count(self)==0:
      self.listener.append(piece)
      piece.relation.append(self)
    logging.info("Square %ix%i: Listener data; %s"%(self.x,self.y,str(['%ix%i'%(p.square.x,p.square.y) for p in self.listener])))
    
  def removeListener(self,piece):
    logging.info("Square %ix%i: Removing listener %ix%i."%(self.x,self.y,piece.square.x,piece.square.y))
    logging.info("Square %ix%i: Listener data; %s"%(self.x,self.y,str(['%ix%i'%(p.square.x,p.square.y) for p in self.listener])))
    if self.listener.count(piece): self.listener.remove(piece)
    logging.info("Square %ix%i: Listener data; %s"%(self.x,self.y,str(['%ix%i'%(p.square.x,p.square.y) for p in self.listener])))
    
  def addMove(self,piece):
    logging.info("Square %ix%i: Piece-%ix%i will be added as move.Count(%i)"%(self.x,self.y,piece.square.x,piece.square.y,self.move.count(piece)))
    logging.info("Square %ix%i: Move data before adding; %s"%(self.x,self.y,str(['%ix%i'%(p.square.x,p.square.y) for p in self.move])))
    if self.move.count(piece)==0: self.move.append(piece)
    if piece.movement.count(self)==0: piece.movement.append(self)
    logging.info("Square %ix%i: Move data; %s"%(self.x,self.y,str(['%ix%i'%(p.square.x,p.square.y) for p in self.move])))
    logging.info("Piece %ix%i: Move data; %s"%(piece.square.x,piece.square.y,str(['%ix%i'%(square.x,square.y) for square in piece.movement])))
    
  def removeMove(self,piece):
    logging.info("Square %ix%i: Removing move %ix%i."%(self.x,self.y,piece.square.x,piece.square.y))
    logging.info("Square %ix%i: move data: %s"%(self.x,self.y,str(['%ix%i'%(p.square.x,p.square.y) for p in self.move])))
    if self.move.count(piece): self.move.remove(piece)
    if piece.movement.count(self): piece.movement.remove(self)
    logging.info("Square %ix%i: move data: %s"%(self.x,self.y,str(['%ix%i'%(p.square.x,p.square.y) for p in self.move])))
    logging.info("Piece %ix%i: Move data; %s"%(piece.square.x,piece.square.y,str(['%ix%i'%(square.x,square.y) for square in piece.movement])))
      
  def addThreat(self,piece):
    logging.info("Square %ix%i: Adding %ix%i as threat."%(self.x,self.y,piece.square.x,piece.square.y))
    if piece.threat.count(self)==0:
      self.threat.append(piece)
      piece.threat.append(self)
    logging.info("Square %ix%i: Threat data; %s"%(self.x,self.y,str(['%ix%i'%(p.square.x,p.square.y) for p in self.threat])))
    
  def removeThreat(self,piece):
    logging.info("Square %ix%i: Removing threat %ix%i."%(self.x,self.y,piece.square.x,piece.square.y))
    logging.info("Square %ix%i: Threat data: %s"%(self.x,self.y,str(['%ix%i'%(p.square.x,p.square.y) for p in self.threat])))
    if self.threat.count(piece): self.threat.remove(piece)
    
  def setPiece(self,piece):
    if self.piece:
      self.piece.remove()
    piece.square = self
    piece.history.append(self)
    self.piece = piece
