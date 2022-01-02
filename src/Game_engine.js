import React, { useState } from 'react'
import Board from './components/Board'
import bbishop from './chessIcons/bbishop.png'
import wbishop from './chessIcons/wbishop.png'
import bknight from './chessIcons/bknight.png'
import wknight from './chessIcons/wknight.png'
import brook from './chessIcons/brook.png'
import wrook from './chessIcons/wrook.png'
import bking from './chessIcons/bking.png'
import wking from './chessIcons/wking.png'
import bqueen from './chessIcons/bqueen.png'
import wqueen from './chessIcons/wqueen.png'
import bpawn from './chessIcons/bpawn.png'
import wpawn from './chessIcons/wpawn.png'
import { isCompositeComponent } from 'react-dom/cjs/react-dom-test-utils.production.min'

class Game_engine extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      //contains info on each square for the current board
      //id is the square identifier: 1 is top right, 8 is top left, 64 is bottom right
      //square color doesnt actually do anything, im just too lazy to remove it from everywhere
      //piece signifies which piece is on each square: 0=none, 1=pawn, 2=bishop, 3=knight, 4=rook, 5=queen, 6=king
      //pieceColor signfies which team the piece is on: true=white, false=black, ''=none
      //icon is the graphics component to display the piece on each square
      squares:[{
            id:1,
            squareColor:true,
            piece: 4,
            pieceColor: false,
            icon: <img src={brook} className="piece-img" alt="brook"/>,
        },
        {
            id:2,
            squareColor:false,
            piece: 3,
            pieceColor: false,
            icon: <img src={bknight} className="piece-img" alt="bknight"/>,
        },
        {
            id:3,
            squareColor:true,
            piece: 2,
            pieceColor: false,
            icon: <img src={bbishop} className="piece-img" alt="bbishop"/>,
        },
        {
            id:4,
            squareColor:false,
            piece: 5,
            pieceColor: false,
            icon: <img src={bqueen} className="piece-img" alt="bqueen"/>,
        },
        {
            id:5,
            squareColor:true,
            piece: 6,
            pieceColor: false,
            icon: <img src={bking} className="piece-img" alt="bking"/>,
        },
        {
            id:6,
            squareColor:false,
            piece: 2,
            pieceColor: false,
            icon: <img src={bbishop} className="piece-img" alt="bbishop"/>,
        },
        {
            id:7,
            squareColor:true,
            piece: 3,
            pieceColor: false,
            icon: <img src={bknight} className="piece-img" alt="bknight"/>,
        },
        {
            id:8,
            squareColor:false,
            piece: 4,
            pieceColor: false,
            icon: <img src={brook} className="piece-img" alt="brook"/>,
        },
        {
            id:9,
            squareColor:true,
            piece: 1,
            pieceColor: false,
            icon: <img src={bpawn} className="piece-img" alt="bpawn"/>,
        },
        {
            id:10,
            squareColor:false,
            piece: 1,
            pieceColor: false,
            icon: <img src={bpawn} className="piece-img" alt="bpawn"/>,
        },
        {
            id:11,
            squareColor:true,
            piece: 1,
            pieceColor: false,
            icon: <img src={bpawn} className="piece-img" alt="bpawn"/>,
        },
        {
            id:12,
            squareColor:false,
            piece: 1,
            pieceColor: false,
            icon: <img src={bpawn} className="piece-img" alt="bpawn"/>,
        },
        {
            id:13,
            squareColor:true,
            piece: 1,
            pieceColor: false,
            icon: <img src={bpawn} className="piece-img" alt="bpawn"/>,
        },
        {
            id:14,
            squareColor:false,
            piece: 1,
            pieceColor: false,
            icon: <img src={bpawn} className="piece-img" alt="bpawn"/>,
        },
        {
            id:15,
            squareColor:true,
            piece: 1,
            pieceColor: false,
            icon: <img src={bpawn} className="piece-img" alt="bpawn"/>,
        },
        {
            id:16,
            squareColor:false,
            piece: 1,
            pieceColor: false,
            icon: <img src={bpawn} className="piece-img" alt="bpawn"/>,
        },
        {
            id:17,
            squareColor:true,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:18,
            squareColor:false,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:19,
            squareColor:true,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:20,
            squareColor:false,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:21,
            squareColor:true,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:22,
            squareColor:false,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:23,
            squareColor:true,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:24,
            squareColor:false,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:25,
            squareColor:true,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:26,
            squareColor:false,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:27,
            squareColor:true,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:28,
            squareColor:false,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:29,
            squareColor:true,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:30,
            squareColor:false,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:31,
            squareColor:true,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:32,
            squareColor:false,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:33,
            squareColor:true,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:34,
            squareColor:false,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:35,
            squareColor:true,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:36,
            squareColor:false,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:37,
            squareColor:true,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:38,
            squareColor:false,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:39,
            squareColor:true,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:40,
            squareColor:false,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:41,
            squareColor:true,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:42,
            squareColor:false,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:43,
            squareColor:true,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:44,
            squareColor:false,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:45,
            squareColor:true,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:46,
            squareColor:false,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:47,
            squareColor:true,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:48,
            squareColor:false,
            piece: 0,
            pieceColor: '',
            icon: '',
        },
        {
            id:49,
            squareColor:true,
            piece: 1,
            pieceColor: true,
            icon: <img src={wpawn} className="piece-img" alt="wpawn"/>,
        },
        {
            id:50,
            squareColor:false,
            piece: 1,
            pieceColor: true,
            icon: <img src={wpawn} className="piece-img" alt="wpawn"/>,
        },
        {
            id:51,
            squareColor:true,
            piece: 1,
            pieceColor: true,
            icon: <img src={wpawn} className="piece-img" alt="wpawn"/>,
        },
        {
            id:52,
            squareColor:false,
            piece: 1,
            pieceColor: true,
            icon: <img src={wpawn} className="piece-img" alt="wpawn"/>,
        },
        {
            id:53,
            squareColor:true,
            piece: 1,
            pieceColor: true,
            icon: <img src={wpawn} className="piece-img" alt="wpawn"/>,
        },
        {
            id:54,
            squareColor:false,
            piece: 1,
            pieceColor: true,
            icon: <img src={wpawn} className="piece-img" alt="wpawn"/>,
        },
        {
            id:55,
            squareColor:true,
            piece: 1,
            pieceColor: true,
            icon: <img src={wpawn} className="piece-img" alt="wpawn"/>,
        },
        {
            id:56,
            squareColor:false,
            piece: 1,
            pieceColor: true,
            icon: <img src={wpawn} className="piece-img" alt="wpawn"/>,
        },
        {
            id:57,
            squareColor:true,
            piece: 4,
            pieceColor: true,
            icon: <img src={wrook} className="piece-img" alt="wrook"/>,
        },
        {
            id:58,
            squareColor:false,
            piece: 3,
            pieceColor: true,
            icon: <img src={wknight} className="piece-img" alt="wknight"/>,
        },
        {
            id:59,
            squareColor:true,
            piece: 2,
            pieceColor: true,
            icon: <img src={wbishop} className="piece-img" alt="wbishop"/>,
        },
        {
            id:60,
            squareColor:false,
            piece: 5,
            pieceColor: true,
            icon: <img src={wqueen} className="piece-img" alt="wqueen"/>,
        },
        {
            id:61,
            squareColor:true,
            piece: 6,
            pieceColor: true,
            icon: <img src={wking} className="piece-img" alt="wking"/>,
        },
        {
            id:62,
            squareColor:false,
            piece: 2,
            pieceColor: true,
            icon: <img src={wbishop} className="piece-img" alt="wbishop"/>,
        },
        {
            id:63,
            squareColor:true,
            piece: 3,
            pieceColor: true,
            icon: <img src={wknight} className="piece-img" alt="wknight"/>,
        },
        {
            id:64,
            squareColor:false,
            piece: 4,
            pieceColor: true,
            icon: <img src={wrook} className="piece-img" alt="wrook"/>,
        },
      ],
      //moves, contains the current moves that can be made by the current selected piece
      moves:[],
      //selectedPiece is a list where the first element signifies if a piece is selected and the second is the data for that piece
      selectedPiece:[false, 
        {
          id:0,
          squareColor:true,
          piece: 0,
          pieceColor: '',
          icon: '',
        }
      ],
      //turn signifies whos turn is it: true=white, false:black
      turn:true,
      //enpassent signifies which square (by id) enpassent can occur: 0=cannot happen
      enpassent:0,
      //castling determines right to castling based only on if kings and rook have been moved: 
      //wlong, wshort, blong, bshort
      castling:[true,true,true,true],
      //checkmate signifies if checkmate has occured and one team is out of moves and in check
      checkmate:false,
      //stalemate signifies if stalemate has occured and one team is out of moves and but not in check
      stalemate:false,
      //draw determines if a draw has occured, either by repitition or by 50 move rule
      draw:false,
      //move50 determines how many moves it's been since a pawn move or capture, keeps track for 50 move rule
      move50:0,
      //keeps track of all board states already reached to determine if a postition has been reach 3 times already
      history:[],
      //determines if game is waiting for a promotion piece to be chosen
      promoting:false,
      //saves the move that was being made when asking about promotion
      promoteSavedSquare: {
        id:0,
        squareColor:true,
        piece: 0,
        pieceColor: '',
        icon: '',
      },
    }
  }

  //a function that does nothing
  nothing() {}

  //called when a square has been clicked on
  //determines if the game is still being played and if the user is trying to make a move or select a piece
  selecting(square) {
    if(this.state.turn) {
      (this.state.promoting ?
        (this.nothing()) : //random function that does actually nothin
        ((this.state.checkmate || this.state.stalemate || this.state.draw) ? 
          this.unselect() :
          (this.state.selectedPiece[0] ? this.checkMove(square) : this.pickPiece(square))))
    }
  }

  //called when a piece is being moved to a legal square
  //updates the board and game state variables
  makeMove(square) {
    // console.log(evaluatePos(this.state.squares, this.state.castling, this.state.enpassent, this.state.turn))
    // console.log(engine_moves(this.state.squares, this.state.castling, this.state.enpassent, this.state.turn, this.state.history, this.state.move50, 0, true))

    //------updating board, and game states other than those which singify the end of the game------
    if (isEnpassent(square, this.state.selectedPiece[1])) {//for enpassent moves
      this.setState({
        //adds the previous position to the history
        history:this.state.history.concat([this.state.squares]),
        //updates the board
        squares: this.state.squares.map((squareCheck) => {
          if (squareCheck.id === square.id) { //moves the piece to the new square
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: this.state.selectedPiece[1].piece,
              pieceColor: this.state.selectedPiece[1].pieceColor,
              icon: this.state.selectedPiece[1].icon,
            }
          } else if  (squareCheck.id === this.state.selectedPiece[1].id) { //resets the square the piece is moving from
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          } else if (squareCheck.id === this.state.enpassent) { //deletes the pawn on enpassent square
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          } else { //stays the same if the square is unaffected by the move
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: squareCheck.piece,
              pieceColor: squareCheck.pieceColor,
              icon: squareCheck.icon,
            }
          }
        }),
        //unselectes the piece
        selectedPiece:[false, 
          {
            id:0,
            squareColor:true,
            piece: 0,
            pieceColor: '',
            icon: '',
          }
        ],
        //removes all move possibilities since no piece is selected
        moves:[],
        //makes it the pther players turn
        turn:!this.state.turn,
        //resets enpassent since a pawn couldnt have moved up 2 squares
        enpassent: 0,
        //resets 50 move rule since a pawn was moved and piece was taken
        move50: 0,
      })
    } else if(isCastle(square, this.state.selectedPiece[1])) { //for castling

      //variable to store the id of the square the piece is currently on
      var num=this.state.selectedPiece[1].id

      //initilaizes ids for where the rook is moving
      var oldId
      var newId
      //determiens the ids of the rook movements 
      if(this.state.selectedPiece[1].pieceColor && num+2 === square.id) { //white castle short
        newId=62
        oldId=64
      } else if(this.state.selectedPiece[1].pieceColor && num-2 === square.id) {  //white castle long
        newId=60
        oldId=57
      } else if(!this.state.selectedPiece[1].pieceColor && num+2 === square.id) { //black castle short
        newId=6
        oldId=8
      } else { //black castle long
        newId=4
        oldId=1
      }

      //creates sqaure to identity which square on the board matchs it when moving the pieces
      //only the id is needed for the one
      var newRook = {
        id:newId
      }
      //creates sqaure to identity which square on the board matchs it when moving the pieces
      var oldRook = {
        id:oldId,
        squareColor:getSquare(oldId, this.state.squares).squareColor,
        piece: getSquare(oldId, this.state.squares).piece,
        pieceColor: getSquare(oldId, this.state.squares).pieceColor,
        icon: getSquare(oldId, this.state.squares).icon,
      }

      this.setState({
        //adds the previous position to the history
        history:this.state.history.concat([this.state.squares]),
        //makes the appropriate teams castling rights false
        castling: this.state.selectedPiece[1].pieceColor ? [false, false, this.state.castling[2], this.state.castling[3]] : [this.state.castling[0], this.state.castling[1], false, false],
        enpassent: 0,
        //updates the board
        squares: this.state.squares.map((squareCheck) => {
          if (squareCheck.id === square.id) { //moves the king to the new square
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: this.state.selectedPiece[1].piece,
              pieceColor: this.state.selectedPiece[1].pieceColor,
              icon: this.state.selectedPiece[1].icon,
            }
          } else if  (squareCheck.id === this.state.selectedPiece[1].id) {//resets the square the king is moving from
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          } else if(squareCheck.id === oldRook.id) { //resets the square the rook is moving from
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          } else if(squareCheck.id === newRook.id) { //moves the rook to the new square
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: oldRook.piece,
              pieceColor: oldRook.pieceColor,
              icon: oldRook.icon,
            }
          } else {//stays the same if the square is unaffected by the move
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: squareCheck.piece,
              pieceColor: squareCheck.pieceColor,
              icon: squareCheck.icon,
            }
          }
        }),
        //unselectes the king
        selectedPiece:[false, 
          {
            id:0,
            squareColor:true,
            piece: 0,
            pieceColor: '',
            icon: '',
          }
        ],
        //removes all move possibilities since no piece is selected
        moves:[],
        //makes it the pther players turn
        turn:!this.state.turn,
        //updates 50 move rule since no pawn was moved and a piece couldnt have been taken
        move50: this.state.move50+0.5,
      })
    } else if(isPromotion(this.state.selectedPiece[1])) {//for promoting

      //saves move data and waits for promotion to be chosen
      this.setState({ promoting:true, promoteSavedSquare:{
        id:square.id,
        squareColor:square.squareColor,
        piece: square.piece,
        pieceColor: square.pieceColor,
        icon: square.icon,
      }}) 
    } else {//for normal moves
      this.setState({
        //adds the previous position to the history
        history:this.state.history.concat([this.state.squares]),
        //determines how the 50 move rule should be updated
        enpassent: (Math.abs(square.id-this.state.selectedPiece[1].id)===16 && this.state.selectedPiece[1].piece===1) ? square.id : 0,
        //updates the board
        squares: this.state.squares.map((squareCheck) => {
          if (squareCheck.id === square.id) { //moves the piece to the new square
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: this.state.selectedPiece[1].piece,
              pieceColor: this.state.selectedPiece[1].pieceColor,
              icon: this.state.selectedPiece[1].icon,
            }
          } else if  (squareCheck.id === this.state.selectedPiece[1].id) {//resets the square the piece is moving from
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          } else { //stays the same if the square is unaffected by the move
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: squareCheck.piece,
              pieceColor: squareCheck.pieceColor,
              icon: squareCheck.icon,
            }
          }
        }),
        //unselectes the piece
        selectedPiece:[false, 
          {
            id:0,
            squareColor:true,
            piece: 0,
            pieceColor: '',
            icon: '',
          }
        ],
        //removes all move possibilities since no piece is selected
        moves:[],
        //makes it the pther players turn
        turn:!this.state.turn,
        //updates castling as needed: if a rook or king are moved
        castling:changeCastle(this.state.selectedPiece[1], square, this.state.castling),
        //updates the 50 move rule as needed
        move50: (square.piece !== 0 || this.state.selectedPiece[1].piece === 1) ? 0 : this.state.move50 + 0.5,
      })
    }

    //------updates the game ending game states------

    if(!isPromotion(this.state.selectedPiece[1])) {
      //makes a new board where the move is made and able to be used
      var newSquares = pretendMove(square, this.state.selectedPiece[1], this.state.squares, this.state.enpassent)
      //determines the new 50 move rule count after the previous is made
      var newMove50 = (square.piece !== 0 || this.state.selectedPiece[1].piece === 1) ? 0 : this.state.move50+0.5
      var newEnpassent = (Math.abs(square.id-this.state.selectedPiece[1].id)===16 && this.state.selectedPiece[1].piece===1) ? square.id : 0

      //determines if the next player has any moves
      if(isOver(newSquares, !this.state.turn, this.state.castling, newEnpassent)) {
      
        //determines if it is checkmate or stalemate
        if (inCheck(newSquares, !this.state.turn, this.state.castling, newEnpassent)) {
        //turn wins
        this.setState({ checkmate:true })
        } else {
        //stalemate
        this.setState({ stalemate:true })
        }
      //determines of there is a draw by repitition or 50 move rule
      } else if(newMove50===50 || numAppearsBoard(newSquares, this.state.history) >= 2) {
        this.setState({ draw:true })
      }

      var newCastling = changeCastle(this.state.selectedPiece[1], square, this.state.castling)
      var newHistory = this.state.history.concat([this.state.squares])
      //bot makes move
      this.botMove(newSquares, newCastling, newEnpassent, newHistory, newMove50, !this.state.turn)
    }
  }

  //called when a piece is being unselected but has clicked on another piece that the user may be trying to select
  //either completely deselects everything or deselects and reselects
  unselectMaybe(square) {
    //determines if a new piece is being selected
    (square.piece && square.pieceColor===this.state.turn) ?
      this.setState({ //if selecting new piece
        moves:findMoves(square, this.state.squares, this.state.castling, this.state.enpassent),
        selectedPiece:[true,
          {
            id:square.id,
            squareColor:square.squareColor,
            piece:square.piece,
            pieceColor: square.pieceColor,
            icon: square.icon,
          }
        ],
      }) :
      this.unselect() //if just deselecting
  }

  //called when a piece is being clicked off of and unselected
  //updates the selectedPiece and moves data
  unselect() {
    this.setState({
      moves:[],
      selectedPiece: [ false,
        {
          id:0,
          squareColor:true,
          piece: 0,
          pieceColor: '',
          icon: '',
        }
      ]}) 
  }

  //called when a piece hadnt been already selected but now is
  //updates the selectedPiece and moves data
  select(square) {
    this.setState({
      moves:findMoves(square, this.state.squares, this.state.castling, this.state.enpassent),
      selectedPiece:[true,
        {
          id:square.id,
          squareColor:square.squareColor,
          piece:square.piece,
          pieceColor: square.pieceColor,
          icon: square.icon,
        }
      ]
    }) 
  }

  //called when a move may be trying to be made and determines if the move is legal
  checkMove(square) {
    this.state.moves.includes(square.id) ?
      this.makeMove(square) : //when move made is legal
      this.unselectMaybe(square) //when move made is illegal
  }

  //called the board is clicked on but no piece has been selected yet
  //determines which is the correct function to call
  pickPiece(square) {
    (square.piece && square.pieceColor===this.state.turn) ? 
      this.select(square) : //when clicked on piece
      this.unselect() //when clicked on empty square or wrong team
  }

  pickPromotion(piece){

    //----------updates board state ------------
    if(this.state.selectedPiece[1].pieceColor){//white
      switch (piece) {
        case 2: //bishop
          this.setState({
            //adds the previous position to the history
            history:this.state.history.concat([this.state.squares]),
            //determines how the 50 move rule should be updated
            enpassent: 0,
            //updates the board
            squares: this.state.squares.map((squareCheck) => {
              if (squareCheck.id === this.state.promoteSavedSquare.id) { //moves the piece to the new square
                return {
                  id:squareCheck.id,
                  squareColor:squareCheck.squareColor,
                  piece: 2,
                  pieceColor: this.state.selectedPiece[1].pieceColor,
                  icon: <img src={wbishop} className="piece-img" alt="wbishop"/>,
                }
              } else if  (squareCheck.id === this.state.selectedPiece[1].id) {//resets the square the piece is moving from
                return {
                  id:squareCheck.id,
                  squareColor:squareCheck.squareColor,
                  piece: 0,
                  pieceColor: '',
                  icon: '',
                }
              } else { //stays the same if the square is unaffected by the move
                return {
                  id:squareCheck.id,
                  squareColor:squareCheck.squareColor,
                  piece: squareCheck.piece,
                  pieceColor: squareCheck.pieceColor,
                  icon: squareCheck.icon,
                }
              }
            }),
            //unselectes the piece
            selectedPiece:[false, 
              {
                id:0,
                squareColor:true,
                piece: 0,
                pieceColor: '',
                icon: '',
              }
            ],
            //removes all move possibilities since no piece is selected
            moves:[],
            //makes it the pther players turn
            turn:!this.state.turn,
            //updates the 50 move rule as needed
            move50: 0,
            //resets promotion stuff
            promoting: false,
            promotion:0,
            promoteSavedSquare:{
              id:0,
              squareColor:true,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          })
          break;
        case 3: //knight
          this.setState({
            //adds the previous position to the history
            history:this.state.history.concat([this.state.squares]),
            //determines how the 50 move rule should be updated
            enpassent: 0,
            //updates the board
            squares: this.state.squares.map((squareCheck) => {
              if (squareCheck.id === this.state.promoteSavedSquare.id) { //moves the piece to the new square
                return {
                  id:squareCheck.id,
                  squareColor:squareCheck.squareColor,
                  piece: 3,
                  pieceColor: this.state.selectedPiece[1].pieceColor,
                  icon: <img src={wknight} className="piece-img" alt="wknight"/>,
                }
              } else if  (squareCheck.id === this.state.selectedPiece[1].id) {//resets the square the piece is moving from
                return {
                  id:squareCheck.id,
                  squareColor:squareCheck.squareColor,
                  piece: 0,
                  pieceColor: '',
                  icon: '',
                }
              } else { //stays the same if the square is unaffected by the move
                return {
                  id:squareCheck.id,
                  squareColor:squareCheck.squareColor,
                  piece: squareCheck.piece,
                  pieceColor: squareCheck.pieceColor,
                  icon: squareCheck.icon,
                }
              }
            }),
            //unselectes the piece
            selectedPiece:[false, 
              {
                id:0,
                squareColor:true,
                piece: 0,
                pieceColor: '',
                icon: '',
              }
            ],
            //removes all move possibilities since no piece is selected
            moves:[],
            //makes it the pther players turn
            turn:!this.state.turn,
            //updates the 50 move rule as needed
            move50: 0,
            //resets promotion stuff
            promoting: false,
            promotion:0,
            promoteSavedSquare:{
              id:0,
              squareColor:true,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          })
          break;
        case 4: //rook
          this.setState({
            //adds the previous position to the history
            history:this.state.history.concat([this.state.squares]),
            //determines how the 50 move rule should be updated
            enpassent: 0,
            //updates the board
            squares: this.state.squares.map((squareCheck) => {
              if (squareCheck.id === this.state.promoteSavedSquare.id) { //moves the piece to the new square
                return {
                  id:squareCheck.id,
                  squareColor:squareCheck.squareColor,
                  piece: 4,
                  pieceColor: this.state.selectedPiece[1].pieceColor,
                  icon: <img src={wrook} className="piece-img" alt="wrook"/>,
                }
              } else if  (squareCheck.id === this.state.selectedPiece[1].id) {//resets the square the piece is moving from
                return {
                  id:squareCheck.id,
                  squareColor:squareCheck.squareColor,
                  piece: 0,
                  pieceColor: '',
                  icon: '',
                }
              } else { //stays the same if the square is unaffected by the move
                return {
                  id:squareCheck.id,
                  squareColor:squareCheck.squareColor,
                  piece: squareCheck.piece,
                  pieceColor: squareCheck.pieceColor,
                  icon: squareCheck.icon,
                }
              }
            }),
            //unselectes the piece
            selectedPiece:[false, 
              {
                id:0,
                squareColor:true,
                piece: 0,
                pieceColor: '',
                icon: '',
              }
            ],
            //removes all move possibilities since no piece is selected
            moves:[],
            //makes it the pther players turn
            turn:!this.state.turn,
            //updates the 50 move rule as needed
            move50: 0,
            //resets promotion stuff
            promoting: false,
            promotion:0,
            promoteSavedSquare:{
              id:0,
              squareColor:true,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          })
          break;
        case 5: //queen
          this.setState({
            //adds the previous position to the history
            history:this.state.history.concat([this.state.squares]),
            //determines how the 50 move rule should be updated
            enpassent: 0,
            //updates the board
            squares: this.state.squares.map((squareCheck) => {
              if (squareCheck.id === this.state.promoteSavedSquare.id) { //moves the piece to the new square
                return {
                  id:squareCheck.id,
                  squareColor:squareCheck.squareColor,
                  piece: 5,
                  pieceColor: this.state.selectedPiece[1].pieceColor,
                  icon: <img src={wqueen} className="piece-img" alt="wqueen"/>,
                }
              } else if  (squareCheck.id === this.state.selectedPiece[1].id) {//resets the square the piece is moving from
                return {
                  id:squareCheck.id,
                  squareColor:squareCheck.squareColor,
                  piece: 0,
                  pieceColor: '',
                  icon: '',
                }
              } else { //stays the same if the square is unaffected by the move
                return {
                  id:squareCheck.id,
                  squareColor:squareCheck.squareColor,
                  piece: squareCheck.piece,
                  pieceColor: squareCheck.pieceColor,
                  icon: squareCheck.icon,
                }
              }
            }),
            //unselectes the piece
            selectedPiece:[false, 
              {
                id:0,
                squareColor:true,
                piece: 0,
                pieceColor: '',
                icon: '',
              }
            ],
            //removes all move possibilities since no piece is selected
            moves:[],
            //makes it the pther players turn
            turn:!this.state.turn,
            //updates the 50 move rule as needed
            move50: 0,
            //resets promotion stuff
            promoting: false,
            promotion:0,
            promoteSavedSquare:{
              id:0,
              squareColor:true,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          })
          break;
      }
    } else {//black
      switch (piece) {
        case 2: //bishop
          this.setState({
            //adds the previous position to the history
            history:this.state.history.concat([this.state.squares]),
            //determines how the 50 move rule should be updated
            enpassent: 0,
            //updates the board
            squares: this.state.squares.map((squareCheck) => {
              if (squareCheck.id === this.state.promoteSavedSquare.id) { //moves the piece to the new square
                return {
                  id:squareCheck.id,
                  squareColor:squareCheck.squareColor,
                  piece: 2,
                  pieceColor: this.state.selectedPiece[1].pieceColor,
                  icon: <img src={bbishop} className="piece-img" alt="bbishop"/>,
                }
              } else if  (squareCheck.id === this.state.selectedPiece[1].id) {//resets the square the piece is moving from
                return {
                  id:squareCheck.id,
                  squareColor:squareCheck.squareColor,
                  piece: 0,
                  pieceColor: '',
                  icon: '',
                }
              } else { //stays the same if the square is unaffected by the move
                return {
                  id:squareCheck.id,
                  squareColor:squareCheck.squareColor,
                  piece: squareCheck.piece,
                  pieceColor: squareCheck.pieceColor,
                  icon: squareCheck.icon,
                }
              }
            }),
            //unselectes the piece
            selectedPiece:[false, 
              {
                id:0,
                squareColor:true,
                piece: 0,
                pieceColor: '',
                icon: '',
              }
            ],
            //removes all move possibilities since no piece is selected
            moves:[],
            //makes it the pther players turn
            turn:!this.state.turn,
            //updates the 50 move rule as needed
            move50: 0,
            //resets promotion stuff
            promoting: false,
            promotion:0,
            promoteSavedSquare:{
              id:0,
              squareColor:true,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          })
          break;
        case 3: //knight
          this.setState({
            //adds the previous position to the history
            history:this.state.history.concat([this.state.squares]),
            //determines how the 50 move rule should be updated
            enpassent: 0,
            //updates the board
            squares: this.state.squares.map((squareCheck) => {
              if (squareCheck.id === this.state.promoteSavedSquare.id) { //moves the piece to the new square
                return {
                  id:squareCheck.id,
                  squareColor:squareCheck.squareColor,
                  piece: 3,
                  pieceColor: this.state.selectedPiece[1].pieceColor,
                  icon: <img src={bknight} className="piece-img" alt="bknight"/>,
                }
              } else if  (squareCheck.id === this.state.selectedPiece[1].id) {//resets the square the piece is moving from
                return {
                  id:squareCheck.id,
                  squareColor:squareCheck.squareColor,
                  piece: 0,
                  pieceColor: '',
                  icon: '',
                }
              } else { //stays the same if the square is unaffected by the move
                return {
                  id:squareCheck.id,
                  squareColor:squareCheck.squareColor,
                  piece: squareCheck.piece,
                  pieceColor: squareCheck.pieceColor,
                  icon: squareCheck.icon,
                }
              }
            }),
            //unselectes the piece
            selectedPiece:[false, 
              {
                id:0,
                squareColor:true,
                piece: 0,
                pieceColor: '',
                icon: '',
              }
            ],
            //removes all move possibilities since no piece is selected
            moves:[],
            //makes it the pther players turn
            turn:!this.state.turn,
            //updates the 50 move rule as needed
            move50: 0,
            //resets promotion stuff
            promoting: false,
            promotion:0,
            promoteSavedSquare:{
              id:0,
              squareColor:true,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          })
          break;
        case 4: //rook
          this.setState({
            //adds the previous position to the history
            history:this.state.history.concat([this.state.squares]),
            //determines how the 50 move rule should be updated
            enpassent: 0,
            //updates the board
            squares: this.state.squares.map((squareCheck) => {
              if (squareCheck.id === this.state.promoteSavedSquare.id) { //moves the piece to the new square
                return {
                  id:squareCheck.id,
                  squareColor:squareCheck.squareColor,
                  piece: 4,
                  pieceColor: this.state.selectedPiece[1].pieceColor,
                  icon: <img src={brook} className="piece-img" alt="brook"/>,
                }
              } else if  (squareCheck.id === this.state.selectedPiece[1].id) {//resets the square the piece is moving from
                return {
                  id:squareCheck.id,
                  squareColor:squareCheck.squareColor,
                  piece: 0,
                  pieceColor: '',
                  icon: '',
                }
              } else { //stays the same if the square is unaffected by the move
                return {
                  id:squareCheck.id,
                  squareColor:squareCheck.squareColor,
                  piece: squareCheck.piece,
                  pieceColor: squareCheck.pieceColor,
                  icon: squareCheck.icon,
                }
              }
            }),
            //unselectes the piece
            selectedPiece:[false, 
              {
                id:0,
                squareColor:true,
                piece: 0,
                pieceColor: '',
                icon: '',
              }
            ],
            //removes all move possibilities since no piece is selected
            moves:[],
            //makes it the pther players turn
            turn:!this.state.turn,
            //updates the 50 move rule as needed
            move50: 0,
            //resets promotion stuff
            promoting: false,
            promotion:0,
            promoteSavedSquare:{
              id:0,
              squareColor:true,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          })
          break;
        case 5: //queen
          this.setState({
            //adds the previous position to the history
            history:this.state.history.concat([this.state.squares]),
            //determines how the 50 move rule should be updated
            enpassent: 0,
            //updates the board
            squares: this.state.squares.map((squareCheck) => {
              if (squareCheck.id === this.state.promoteSavedSquare.id) { //moves the piece to the new square
                return {
                  id:squareCheck.id,
                  squareColor:squareCheck.squareColor,
                  piece: 5,
                  pieceColor: this.state.selectedPiece[1].pieceColor,
                  icon: <img src={bqueen} className="piece-img" alt="bqueen"/>,
                }
              } else if  (squareCheck.id === this.state.selectedPiece[1].id) {//resets the square the piece is moving from
                return {
                  id:squareCheck.id,
                  squareColor:squareCheck.squareColor,
                  piece: 0,
                  pieceColor: '',
                  icon: '',
                }
              } else { //stays the same if the square is unaffected by the move
                return {
                  id:squareCheck.id,
                  squareColor:squareCheck.squareColor,
                  piece: squareCheck.piece,
                  pieceColor: squareCheck.pieceColor,
                  icon: squareCheck.icon,
                }
              }
            }),
            //unselectes the piece
            selectedPiece:[false, 
              {
                id:0,
                squareColor:true,
                piece: 0,
                pieceColor: '',
                icon: '',
              }
            ],
            //removes all move possibilities since no piece is selected
            moves:[],
            //makes it the pther players turn
            turn:!this.state.turn,
            //updates the 50 move rule as needed
            move50: 0,
            //resets promotion stuff
            promoting: false,
            promotion:0,
            promoteSavedSquare:{
              id:0,
              squareColor:true,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          })
          break;
      }
    }

    //----------updates game ending states -------------
    //makes a new board where the move is made and able to be used
    var newSquares = pretendPromotion(this.state.promoteSavedSquare, this.state.selectedPiece[1], this.state.squares, this.state.enpassent, piece)

    //determines if the next player has any moves
    if(isOver(newSquares, !this.state.turn, this.state.castling, this.state.enpassent)) {

      //determines if it is checkmate or stalemate
      if (inCheck(newSquares, !this.state.turn, this.state.castling, this.state.enpassent)) {
      //turn wins
      this.setState({ checkmate:true })
      } else {
      //stalemate
      this.setState({ stalemate:true })
      }

      //Note: you cant reach a draw after promoting because you mved a pawn and you couldnt have reached an old position
    }

    var newMove50 = 0
    var newEnpassent = 0
    var newCastling = this.state.castling
    var newHistory = this.state.history.concat([this.state.squares])
    this.botMove(newSquares, newCastling, newEnpassent, newHistory, newMove50, !this.state.turn)
  }

  render() {
    return (
      <div className='App'>
        {/*determines what to display above the board: will say whos turn or the result of the game */}
        <h1 className='game-info'>{this.state.draw ? 'Draw' : (this.state.checkmate ? 'Checkmate!' : (this.state.stalemate ? 'Stalemate' : (this.state.turn ? 'White\'s Turn' : 'Black\'s Turn')))}</h1>
        
        {/* Promotion buttons which appear only when promoting */}
        {this.state.promoting ? 
          <div className='buttons'>
            <button
              onClick={() => this.pickPromotion(5)}
              className='btn'
            >
              {'Queen'}
            </button>
            <button
              onClick={() => this.pickPromotion(4)}
              className='btn'
            >
              {'Rook'}
            </button>
            <button
              onClick={() => this.pickPromotion(3)}
              className='btn'
            >
              {'Knight'}
            </button>
            <button
              onClick={() => this.pickPromotion(2)}
              className='btn'
            >
              {'Bishop'}
            </button>
          </div> : <div></div>} 

        <div className="game">
          <Board 
            //data about each square
            squares={this.state.squares}
            //function for what to do when a square is clicked on
            onSelect={this.selecting.bind(this)}
            //data for which moves are legal and should be highlighted
            moves={this.state.moves}
            //data for which square is selected
            selectedNum={this.state.selectedPiece[1].id}
          />
        </div>
        <p className='description'>
          Note: Abbott runs after you play a move and your move will not appear until Abbott comes up with a move. Please wait for him to play (about 1-2 seconds).
        </p>
      </div>
    );
  }

  componentDidUpdate(prevProps, prevState) {
    //blacks turn an the game isnt over
    if(!this.state.turn && !this.state.checkmate && !this.state.stalemate && !this.state.draw && false) {
      this.botMove(this.state.squares, this.state.castling, this.state.enpassent, this.state.history, this.state.move50, this.state.turn)
    }
  }

  botMove(squares, castling, enpassent, history, move50, turn){
    //blacks turn an the game isnt over
    var move = engine(squares, castling, enpassent, history, move50, turn)


    //------updating board, and game states other than those which singify the end of the game------
    if (isEnpassent(move[0], move[1])) {//for enpassent moves
      this.setState({
        //adds the previous position to the history
        history:history.concat([squares]),
        //updates the board
        squares: squares.map((squareCheck) => {
          if (squareCheck.id === move[0].id) { //moves the piece to the new square
            return {
              id:move[0].id,
              squareColor:move[0].squareColor,
              piece: move[0].piece,
              pieceColor: move[0].pieceColor,
              icon: move[0].icon,
            }
          } else if  (squareCheck.id === move[1].id) { //resets the square the piece is moving from
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          } else if (squareCheck.id === enpassent) { //deletes the pawn on enpassent square
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          } else { //stays the same if the square is unaffected by the move
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: squareCheck.piece,
              pieceColor: squareCheck.pieceColor,
              icon: squareCheck.icon,
            }
          }
        }),
        //unselectes the piece
        selectedPiece:[false, 
          {
            id:0,
            squareColor:true,
            piece: 0,
            pieceColor: '',
            icon: '',
          }
        ],
        //removes all move possibilities since no piece is selected
        moves:[],
        //makes it the pther players turn
        turn:!turn,
        //resets enpassent since a pawn couldnt have moved up 2 squares
        enpassent: 0,
        //resets 50 move rule since a pawn was moved and piece was taken
        move50: 0,
      })
    } else if(isCastle(move[0], move[1])) { //for castling

      //variable to store the id of the square the piece is currently on
      var num=move[1].id

      //initilaizes ids for where the rook is moving
      var oldId
      var newId
      //determiens the ids of the rook movements 
      if(move[1].pieceColor && num+2 === move[0].id) { //white castle short
        newId=62
        oldId=64
      } else if(move[1].pieceColor && num-2 === move[0].id) {  //white castle long
        newId=60
        oldId=57
      } else if(!move[1].pieceColor && num+2 === move[0].id) { //black castle short
        newId=6
        oldId=8
      } else { //black castle long
        newId=4
        oldId=1
      }

      //creates sqaure to identity which square on the board matchs it when moving the pieces
      //only the id is needed for the one
      var newRook = {
        id:newId
      }
      //creates sqaure to identity which square on the board matchs it when moving the pieces
      var oldRook = {
        id:oldId,
        squareColor:getSquare(oldId, squares).squareColor,
        piece: getSquare(oldId, squares).piece,
        pieceColor: getSquare(oldId, squares).pieceColor,
        icon: getSquare(oldId, squares).icon,
      }

      this.setState({
        //adds the previous position to the history
        history:history.concat([squares]),
        //makes the appropriate teams castling rights false
        castling: move[1].pieceColor ? [false, false, castling[2], castling[3]] : [castling[0], castling[1], false, false],
        enpassent: 0,
        //updates the board
        squares: squares.map((squareCheck) => {
          if (squareCheck.id === move[0].id) { //moves the king to the new square
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: move[1].piece,
              pieceColor: move[1].pieceColor,
              icon: move[1].icon,
            }
          } else if  (squareCheck.id === move[1].id) {//resets the square the king is moving from
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          } else if(squareCheck.id === oldRook.id) { //resets the square the rook is moving from
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          } else if(squareCheck.id === newRook.id) { //moves the rook to the new square
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: oldRook.piece,
              pieceColor: oldRook.pieceColor,
              icon: oldRook.icon,
            }
          } else {//stays the same if the square is unaffected by the move
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: squareCheck.piece,
              pieceColor: squareCheck.pieceColor,
              icon: squareCheck.icon,
            }
          }
        }),
        //unselectes the king
        selectedPiece:[false, 
          {
            id:0,
            squareColor:true,
            piece: 0,
            pieceColor: '',
            icon: '',
          }
        ],
        //removes all move possibilities since no piece is selected
        moves:[],
        //makes it the pther players turn
        turn:!turn,
        //updates 50 move rule since no pawn was moved and a piece couldnt have been taken
        move50: move50+0.5,
      })
    } else {//for normal moves
      this.setState({
        //adds the previous position to the history
        history:history.concat([squares]),
        //determines how the 50 move rule should be updated
        enpassent: (Math.abs(move[0].id-move[1].id)===16 && move[1].piece===1) ? move[0].id : 0,
        //updates the board
        squares: squares.map((squareCheck) => {
          if (squareCheck.id === move[0].id) { //moves the piece to the new square
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: move[0].piece,
              pieceColor: move[0].pieceColor,
              icon: move[0].icon,
            }
          } else if  (squareCheck.id === move[1].id) {//resets the square the piece is moving from
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          } else { //stays the same if the square is unaffected by the move
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: squareCheck.piece,
              pieceColor: squareCheck.pieceColor,
              icon: squareCheck.icon,
            }
          }
        }),
        //unselectes the piece
        selectedPiece:[false, 
          {
            id:0,
            squareColor:true,
            piece: 0,
            pieceColor: '',
            icon: '',
          }
        ],
        //removes all move possibilities since no piece is selected
        moves:[],
        //makes it the pther players turn
        turn:!turn,
        //updates castling as needed: if a rook or king are moved
        castling:changeCastle(move[1], move[0], castling),
        //updates the 50 move rule as needed
        move50: (move[0].piece !== 0 || move[1].piece === 1) ? 0 : move50 + 0.5,
      })
    }

    //------updates the game ending game states------

    //makes a new board where the move is made and able to be used
    var newSquares = pretendMove(move[0], move[1], squares, enpassent)
    //determines the new 50 move rule count after the previous is made
    var newMove50 = (move[0].piece !== 0 || move[1].piece === 1) ? 0 : move50+0.5
    var newEnpassent = (Math.abs(move[0].id-move[1].id)===16 && move[1].piece===1) ? move[0].id : 0

    //determines if the next player has any moves
    if(isOver(newSquares, !turn, castling, newEnpassent)) {
    
      //determines if it is checkmate or stalemate
      if (inCheck(newSquares, !turn, castling, newEnpassent)) {
      //turn wins
      this.setState({ checkmate:true })
      } else {
      //stalemate
      this.setState({ stalemate:true })
      }
    //determines of there is a draw by repitition or 50 move rule
    } else if(newMove50===50 || numAppearsBoard(newSquares, history) >= 2) {
      this.setState({ draw:true })
    }
  }
}

// ***************** Chess Engine ******************

//TODO always check if Over in engine moves and evalPos

function engine(squares, castling, enpassent, history, move50, turn) {

  var fullMoves = []
  var scores=[]
  var best

  //gets all possible moves by 'turn'
  for (const square of squares) { //loops through all squares in the position looking for pieces of 'turn'
    if (square.pieceColor === turn) {
      //gets all moves the piece can make in the position
      let moves = findMoves(square, squares, castling, enpassent)
      fullMoves = fullMoves.concat(makeFullMove(square, moves, squares))

      //checks through all the moves and saves best eval in new position
      for (const move of moves) {

        //must check for different piece that pawn can promote to
        if(isPromotion(square)) {

          //Note bishop and rook will never be better than queen

          //knight promote
          let newSquares = pretendPromotion(getSquare(move, squares), square, squares, enpassent, 3)
          let knightScore = engine_moves(newSquares, castling, 0, !turn, history.concat([squares]), 0, 0.5, false)

          //queen promote
          newSquares = pretendPromotion(getSquare(move, squares), square, squares, enpassent, 5)
          let queenScore = engine_moves(newSquares, castling, 0, !turn, history.concat([squares]), 0, 0.5, false)

          scores.push(knightScore)
          scores.push(queenScore)

        } else {

          //stores updated game state: squares, castling, enpassent
          let gameState=[[], [], 0]
          gameState=updateGameState(getSquare(move, squares), square, squares, castling, enpassent)
          let newMove50=(getSquare(move, squares).piece !== 0 || square.piece === 1) ? 0 : move50 + 0.5

          //saves the best evaluation if that move is made
          scores.push(engine_moves(gameState[0], gameState[1], gameState[2], !turn, history.concat([squares]), newMove50, 0.5, false))

        }
      }
    }
  }

  //determines which eval is best
  best=Math.max(...scores)

  //finds the move that leads to the best
  let index
  for(const i in scores){
    if(scores[i]===best){
      index=i
    }
  }

  return fullMoves[index]
}

function engine_moves(squares, castling, enpassent, turn, history, move50, inFuture, isAly) {
  const depth = 1

  //base case
  //when depth is integer, positive numbers are good for aly
  if(inFuture>=depth) {
    return -1 * (evaluatePos(squares, castling, enpassent, turn, history, move50))
  }

  var scores=[]
  var best

  //determines if the 'turn' has any moves
  if(isOver(squares, turn, castling, enpassent)) {
      
    //determines if it is checkmate or stalemate
    if (inCheck(squares, turn, castling, enpassent)) { //checkmate
      if(isAly){//aly got mated
        return -Infinity
      }else{//opp got mated
        return Infinity
      }
    } else { //stalemate
      return 0
    }
  //determines of there is a draw by repitition or 50 move rule
  } else if(move50===50 || numAppearsBoard(squares, history) >= 2) { //if drawn by other means
    return 0
  } else { //if the game is not over
    //gets all possible moves by 'turn'
    for (const square of squares) { //loops through all squares in the position looking for pieces of 'turn'
      if (square.pieceColor === turn) {
        //gets all moves the piece can make in the position
        let moves = findMoves(square, squares, castling, enpassent)

        //checks through all the moves and saves best eval in new position
        for (const move of moves) {

          //must check for different piece that pawn can promote to
          if(isPromotion(square)) {

            //Note bishop and rook will never be better than queen

            //knight promote
            let newSquares = pretendPromotion(getSquare(move, squares), square, squares, enpassent, 3)
            let knightScore = engine_moves(newSquares, castling, 0, !turn, history.concat([squares]), 0, inFuture+0.5, !isAly)

            //queen promote
            newSquares = pretendPromotion(getSquare(move, squares), square, squares, enpassent, 5)
            let queenScore = engine_moves(newSquares, castling, 0, !turn, history.concat([squares]), 0, inFuture+0.5, !isAly)

            if(isAly) { //best eval for if aly is making next move
              scores.push(Math.max( knightScore, queenScore ))
            } else { //best eval for if opp is making next move
              scores.push(Math.min( knightScore, queenScore ))
            }

          } else {

            //stores updated game state: squares, castling, enpassent
            let gameState=[[], [], 0]
            gameState=updateGameState(getSquare(move, squares), square, squares, castling, enpassent)
            let newMove50=(getSquare(move, squares).piece !== 0 || square.piece === 1) ? 0 : move50 + 0.5

            //saves the best evaluation if that move is made
            scores.push(engine_moves(gameState[0], gameState[1], gameState[2], !turn, history.concat([squares]), newMove50, inFuture+0.5, !isAly))

          }
        }
      }
    }

    //opp will always be trying to make the eval as low as possible and aly will be trying to maximise it
    //determines which eval is best for 'aly'
    if(isAly) { //best eval for if aly is making next move
      best=Math.max(...scores)
    } else { //best eval for if opp is making next move
      best=Math.min(...scores)
    }
  }

  return best
}

//updates sqaures, castling and enpassent for a move that was made
function updateGameState(newSquare, oldSquare, squares, castling, enpassent) {

  var newSquares = pretendMove(newSquare, oldSquare, squares, enpassent)
  var newEnpassent = (Math.abs(newSquare.id-oldSquare.id)===16 && oldSquare.piece===1) ? newSquare.id : 0
  var newCastling = changeCastle(oldSquare, newSquare, castling)

  return [newSquares, newCastling, newEnpassent]
}

function makeFullMove(oldSquare, moves, squares) {
  var fullMoves = []

  for (const move of moves) {

    let newSquare
    let newSquare2 //for when promotion, there will be two possiblities
    if(isPromotion(oldSquare)) { //when pormotion
      newSquare= {
        id:move,
        squareColor:true,
        piece: 3,
        pieceColor: oldSquare.pieceColor,
        icon: oldSquare.pieceColor ? <img src={wknight} className="piece-img" alt="wknight"/> : <img src={bknight} className="piece-img" alt="bknight"/>,
      }
      newSquare2= {
        id:move,
        squareColor:true,
        piece: 5,
        pieceColor: oldSquare.pieceColor,
        icon: oldSquare.pieceColor ? <img src={wqueen} className="piece-img" alt="wqueen"/> : <img src={bqueen} className="piece-img" alt="bqueen"/>,
      }

      fullMoves.push([newSquare, oldSquare])
      fullMoves.push([newSquare2, oldSquare])
    } else { //when not pormotion
      newSquare={
        id:move,
        squareColor:true,
        piece: oldSquare.piece,
        pieceColor: oldSquare.pieceColor,
        icon: oldSquare.icon
      }

      fullMoves.push([newSquare, oldSquare])
    }
  }

  return fullMoves
}




//evaluates a position, positive is for who plays next move
function evaluatePos(squares, castling, enpassent, turn, history, move50) {
  const initiativeVal = 0

  //determines if the 'turn' has any moves
  if(isOver(squares, turn, castling, enpassent)) {
      
    //determines if it is checkmate or stalemate
    if (inCheck(squares, turn, castling, enpassent)) { //checkmate
      return -Infinity
    } else { //stalemate
      return 0
    }
  //determines of there is a draw by repitition or 50 move rule
  } else if(move50===50 || numAppearsBoard(squares, history) >= 2) { //if drawn by other means
    return 0
  }

  //advantage of playing the next move
  var evaluation = initiativeVal

  evaluation+=evalMat(squares)

  evaluation+=evalControl(squares, castling, enpassent, turn)
  evaluation-=evalControl(squares, castling, enpassent, !turn)

  return evaluation
}

//evaluate king safety and control of squares
function evalControl(squares, castling, enpassent, turn) {

  // console.log(squares)

  const levelVal = 25
  const sameSideVal = 10
  const oppSideVal = 20

  var evaluation = 0

  //finds which moves '!turn' can make
  var oppmoves = []
  for (const square of squares) {
    if (square.pieceColor === !turn) {
      oppmoves = oppmoves.concat(findControl(square, squares, castling, enpassent))
    }
  }

  //finds which squares 'turn' can make
  var alymoves = []
  for (const square of squares) {
    if (square.pieceColor === turn) {
      alymoves = alymoves.concat(findControl(square, squares, castling, enpassent))
    }
  }

  //finds where the king is
  var kpos
  for (const square of squares) {
    if (square.piece === 6 && square.pieceColor === turn) {
      kpos=square.id
    }
  }
  //finds squares near king
  var kmoves = kingControl(getSquare(kpos, squares), squares, castling, enpassent)
  

  //find king safety
  for (const move of kmoves) {
    //level measures how weak the king is
    //starts with 1 to counter act king protection of itself
    let level=1
    level-=numAppears(move, alymoves)
    level+=numAppears(move, oppmoves)

    evaluation-=Math.abs(level*levelVal)
  }

  //determines control of squares
  alymoves=dedupe(alymoves)
  if(turn) { //white
    for (const move of alymoves){
      if (move <= 32) {
        evaluation+=oppSideVal
      } else {
        evaluation+=sameSideVal
      }
    }
  } else { //black
    for (const move of alymoves){
      if (move > 32) {
        evaluation+=oppSideVal
      } else {
        evaluation+=sameSideVal
      }
    }
  }

  return evaluation
}

//evaluates material in a position
function evalMat (squares) {
  const pawnVal = 100
  const bishopVal = 400
  const knightVal = 300
  const rookVal = 500
  const queenVal = 900

  var evaluation = 0
  for (const square of squares) {
    if (square.pieceColor) { //for white
      switch(square.piece) {
        case 1: //pawn
          evaluation+=pawnVal
          break;
        case 2: //bishop
          evaluation+=bishopVal
          break;
        case 3: //knight
          evaluation+=knightVal
          break;
        case 4: //rook
          evaluation+=rookVal
          break;
        case 5: //queen
          evaluation+=queenVal
          break;
        case 6: //king
          break;
      }
    } else { //for black
      switch(square.piece) {
        case 1: //pawn
          evaluation-=pawnVal
          break;
        case 2: //bishop
          evaluation-=bishopVal
          break;
        case 3: //knight
          evaluation-=knightVal
          break;
        case 4: //rook
          evaluation-=rookVal
          break;
        case 5: //queen
          evaluation-=queenVal
          break;
        case 6: //king
          break;
      }
    }
  }

  return evaluation
}

function dedupe(array){
  var unique = []
  
  for (const elem of array) {
    if (!unique.includes(elem)) {
      unique.push(elem)
    }
  }

  return unique
}

//returns the number of times key appears in array
function numAppears(key, array) {
  var count=0
  for (const elem in array) {
    if (elem === key) {
      count++
    }
  }
  return count
}

//finds the sqaures a piece controls
function findControl(square, squares, castling, enpassent) {
  var moves=[]

  // console.log(square)

  switch(square.piece) {
    case 1: //pawn
      moves=pawnControl(square, squares, castling, enpassent)
      break;
    case 2: //bishop
      moves=bishopControl(square, squares, castling, enpassent)
      break;
    case 3: //knight
      moves=knightControl(square, squares, castling, enpassent)
      break;
    case 4: //rook
      moves=rookControl(square, squares, castling, enpassent)
      break;
    case 5: //queen
      let movesD=bishopControl(square, squares, castling, enpassent)
      let movesS=rookControl(square, squares, castling, enpassent)
      moves=movesD.concat(movesS)
      break;
    case 6: //king
      moves=kingControl(square, squares, castling, enpassent)
      break;
  }

  return moves
}

//returns an array of ids a pawn can attack
function pawnControl(square, squares, castling, enpassent) {
  var moves = []
  var num=square.id

  if (square.pieceColor) { //white pawn
    //checks if the pawn can take a piece diagonally left of it
    moves.push(infinityLeft(num-9))
    //checks if the pawn can take a piece diagonally right of it
    moves.push(infinityRight(num-7))
  
  } else { //black pawn
    //checks if the pawn can take a piece diagonally right of it
    moves.push(infinityRight(num+9))
    //checks if the pawn can take a piece diagonally left of it
    moves.push(infinityLeft(num+7))
  }

  //removes all moves where you end up in check
  moves = moves.filter(move => testMove(getSquare(move, squares), square, squares, castling, enpassent, square.pieceColor))
  return moves
}

//returns an array of ids a bishop can attack
function bishopControl(square, squares, castling, enpassent) {
  var moves = []
  var num=square.id

  //loops through all squares protruding out from 'sqaure' in the 4 diagonal diractions until it reaches a piece, or reaches the edge of the board
  var newNum = infinityRight(num+9)
  //checks the the new square is in the right range (1,64), that the new square is not on the same team and that the square last checked wasnt a square where the rook takes
  while (newNum >= 1 && newNum <= 64 && (getSquare(infinityLeft(newNum-9), squares).pieceColor !== square.pieceColor || getSquare(infinityLeft(newNum-9), squares).piece===5 || getSquare(infinityLeft(newNum-9), squares).piece===2) && getSquare(infinityLeft(newNum-9), squares).pieceColor !== !square.pieceColor) {
    moves.push(newNum)
    newNum=infinityRight(newNum+9)
  }
  if(getSquare(infinityLeft(newNum-9), squares).piece===1 && !square.pieceColor) {
    moves.push(newNum)
  }
  //resets the square being checked
  newNum=infinityLeft(num-9)
  while (newNum >= 1 && newNum <= 64 && (getSquare(infinityRight(newNum+9), squares).pieceColor !== square.pieceColor || getSquare(infinityRight(newNum+9), squares).piece===5 || getSquare(infinityRight(newNum+9), squares).piece===2) && getSquare(infinityRight(newNum+9), squares).pieceColor !== !square.pieceColor) {
    moves.push(newNum)
    newNum=infinityLeft(newNum-9)
  }
  if(getSquare(infinityRight(newNum+9), squares).piece===1 && square.pieceColor) {
    moves.push(newNum)
  }
  //resets the square being checked
  newNum=infinityLeft(num+7)
  while (newNum >= 1 && newNum <= 64 && (getSquare(infinityRight(newNum-7), squares).pieceColor !== square.pieceColor || getSquare(infinityRight(newNum-7), squares).piece===5 || getSquare(infinityRight(newNum-7), squares).piece===2) && getSquare(infinityRight(newNum-7), squares).pieceColor !== !square.pieceColor) {
    moves.push(newNum)
    newNum=infinityLeft(newNum+7)
  }
  if(getSquare(infinityRight(newNum-7), squares).piece===1 && !square.pieceColor) {
    moves.push(newNum)
  }
  //resets the square being checked
  newNum=infinityRight(num-7)
  while (newNum >= 1 && newNum <= 64 && (getSquare(infinityLeft(newNum+7), squares).pieceColor !== square.pieceColor || getSquare(infinityLeft(newNum+7), squares).piece===5 || getSquare(infinityLeft(newNum+7), squares).piece===2) && getSquare(infinityLeft(newNum+7), squares).pieceColor !== !square.pieceColor) {
    moves.push(newNum)
    newNum=infinityRight(newNum-7)
  }
  if(getSquare(infinityLeft(newNum+7), squares).piece===1 && square.pieceColor) {
    moves.push(newNum)
  }

  //removes all moves where you end up in check
  moves = moves.filter(move => testMove(getSquare(move, squares), square, squares, castling, enpassent, square.pieceColor))
  return moves
}

//returns an array of ids a knight can attack
function knightControl(square,squares, castling, enpassent) {
  var moves = []
  var num=square.id

  //checks all 8 squares a knight could move to end checks the the square is on the board
  if ((num-1) %8 === 0) { //for when it will wrap across the left side 4 times
    let newNum=num+14
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+10
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+23
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+17
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-6
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-2
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-15
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-9
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
  } else if ((num-1) %8 === 1) { //for when it will wrap across the left side 2 times
    let newNum=num+14
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+10
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+15
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+17
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-6
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-2
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-15
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-17
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
  } else if ((num-1) %8 === 7) { //for when it will wrap across the right side 4 times
    let newNum=num+6
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+2
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+15
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+9
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-14
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-10
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-23
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-17
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
  } else if ((num-1) %8 === 6) { //for when it will wrap across the right side 2 times
    let newNum=num+6
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+2
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+15
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+17
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-14
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-10
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-15
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-17
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
  } else { //for when it will not wrap
    let newNum=num+6
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+10
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+15
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+17
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-6
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-10
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-15
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-17
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
  }

  //removes all moves where you end up in check
  moves = moves.filter(move => testMove(getSquare(move, squares), square, squares, castling, enpassent, square.pieceColor))
  return moves
}

//returns an array of ids a rook can attack
function rookControl(square, squares, castling, enpassent) {
  var moves = []
  var num=square.id

  //loops through all squares protruding out from 'sqaure' in the 4 cardinal diractions until it reaches it's self again, reaches a piece, or reaches the edge of the board
  var newNum = num+8
  //checks the the new square is in the right range (1,64), that the last square checked wasnt its own piece or if it is that it is a queen or rook, that the square last checked wasnt a square where the rook takes, that the horizontal moves dont loop
  while (newNum >= 1 && newNum <= 64 && (getSquare((newNum-8), squares).pieceColor !== square.pieceColor || getSquare((newNum-8), squares).piece === 5 || getSquare((newNum-8), squares).piece === 4) && getSquare(newNum-8, squares).pieceColor !== !square.pieceColor) {
    moves.push(newNum)
    newNum+=8
  }
  //resets the square being checked
  newNum=num-8
  while (newNum >= 1 && newNum <= 64 && (getSquare((newNum+8), squares).pieceColor !== square.pieceColor || getSquare((newNum+8), squares).piece === 5 || getSquare((newNum+8), squares).piece === 4) && getSquare(newNum+8, squares).pieceColor !== !square.pieceColor) {
    moves.push(newNum)
    newNum-=8
  }
  //resets the square being checked
  newNum=infinityRight(num+1)
  while (newNum >= 1 && newNum <= 64 && (getSquare(infinityLeft(newNum-1), squares).pieceColor !== square.pieceColor || getSquare(infinityLeft(newNum-1), squares).piece === 5 || getSquare(infinityLeft(newNum-1), squares).piece === 4) && getSquare(infinityLeft(newNum-1), squares).pieceColor !== !square.pieceColor && square.id !== newNum) {
    moves.push(newNum)
    newNum=infinityRight(newNum+1)
  }
  //resets the square being checked
  newNum=infinityLeft(num-1)
  while (newNum >= 1 && newNum <= 64 && (getSquare(infinityRight(newNum+1), squares).pieceColor !== square.pieceColor || getSquare(infinityRight(newNum+1), squares).piece === 5 || getSquare(infinityRight(newNum+1), squares).piece === 4) && getSquare(infinityRight(newNum+1), squares).pieceColor !== !square.pieceColor && square.id !== newNum) {
    moves.push(newNum)
    newNum=infinityLeft(newNum-1)
  }

  //removes all moves where you end up in check
  moves = moves.filter(move => testMove(getSquare(move, squares), square, squares, castling, enpassent, square.pieceColor))
  return moves
}

//returns an array of ids a king can attack
function kingControl(square, squares, castling, enpassent) {
  var moves=[]
  var num=square.id

  //adds all standard moves to the list
  if((num-1) %8 === 0) {//when infinity wraps on the left side
    var newNum=num+1
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+7
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+8
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-8
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+15
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-7
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+9
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-1
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
  } else if ((num-1) %8 === 7) {//when infinity wraps on the right side
    var newNum=num-7
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-1
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+8
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-8
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+7
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-15
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+1
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-9
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
  } else {//when no wrapping is occuring
    var newNum=num+1
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-1
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+8
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-8
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+7
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-7
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num+9
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
    newNum=num-9
    if(newNum>=1 && newNum<=64){
      moves.push(newNum)
    }
  }

  //removes all moves where you end up in check
  moves = moves.filter(move => testMove(getSquare(move, squares), square, squares, castling, enpassent, square.pieceColor))

  return moves
}

// *************************************************

//returns the number of times a position has already been reached
function numAppearsBoard(squares, history) {
  var count = 0
  //loops through each board in history and determines if the two boards are the same
  for (const squaresCheck of history) {
    if(comapareBoards(squares, squaresCheck)) {
      count++
    }
  }

  return count
}

//determines if two boards are the same or not
function comapareBoards(squares1, squares2) {
  //loops through each square in squares1 and determines if there is an identical square in squares2
  for(const square of squares1) {
    if(!inSquares(square, squares2)) {
      return false
    }
  }
  return true
}

//checks if there is a replica of square in squares
function inSquares(square, squares) {
  //loops through each sqaure in sqaures and determines if the square in squares is the same as the square being checked 
  //by looking at the piece on the square, the ids of the square and the color of the piece
  for(const squareCheck of squares) {
    if(square.id===squareCheck.id && square.piece===squareCheck.piece && square.pieceColor===squareCheck.pieceColor) {
      return true
    }
  }
  return false
}

//return an array of castling rights which have been updated accoring to the piece being moved
function changeCastle(oldSquare, newSquare, castling) {

  //if the piece being moved started on the in any of the corners
  if(oldSquare.id === 1) {
    return [castling[0], castling[1], false, castling[3]]
  } else if(oldSquare.id === 8) {
    return [castling[0], castling[1], castling[2], false]
  } else if(oldSquare.id === 57) {
    return [false, castling[1], castling[2], castling[3]]
  } else if(oldSquare.id === 64) {
    return [castling[0], false, castling[2], castling[3]]

  //if the piece being moved is going to any of the corners
  } else if(newSquare.id === 1) {
    return [castling[0], castling[1], false, castling[3]]
  } else if(newSquare.id === 8) {
    return [castling[0], castling[1], castling[2], false]
  } else if(newSquare.id === 57) {
    return [false, castling[1], castling[2], castling[3]]
  } else if(newSquare.id === 64) {
    return [castling[0], false, castling[2], castling[3]]

  //if a king is being moved
  } else if(oldSquare.piece === 6 && oldSquare.pieceColor) {
    return [false, false, castling[2], castling[3]]
  } else if (oldSquare.piece === 6 && !oldSquare.pieceColor) {
    return [castling[0], castling[1], false, false]
  }

  return castling
}

//checks if an enpassent move is being made
function isEnpassent(newSquare, oldSquare) {

  //check if pawn is being moved
  if(oldSquare.piece===1) { 

    //checks if moved diagonally and newSquare doesnt have a piece on it
    if((infinityRight(oldSquare.id-7)===newSquare.id || infinityRight(oldSquare.id+9)===newSquare.id || infinityLeft(oldSquare.id+7)===newSquare.id || infinityLeft(oldSquare.id-9)===newSquare.id) && newSquare.piece===0) {
      return true
    }
  }
  return false
}

//checks if a castling move was made
function isCastle(newSquare, oldSquare) {

  //checks is piece moves was a king
  if(oldSquare.piece===6) {

    //checks if king didnt make a normal move
    if(infinityRight(oldSquare.id-7)!==newSquare.id && oldSquare.id-8!==newSquare.id && infinityLeft(oldSquare.id-9)!==newSquare.id && infinityRight(oldSquare.id+1)!==newSquare.id && infinityLeft(oldSquare.id-1)!==newSquare.id && infinityLeft(oldSquare.id+7)!==newSquare.id && oldSquare.id+8!==newSquare.id && infinityRight(oldSquare.id+9)!==newSquare.id) {
      return true
    }
  }

  return false
}

//checks if a pawn is being promoted
function isPromotion(oldSquare) {
  var row=Math.ceil(oldSquare.id/8)
  if(oldSquare.piece===1 && ((oldSquare.pieceColor && row===2) || (!oldSquare.pieceColor && row===7))) {
    return true
  } else {
    return false
  }
}

//trys to make a move and sees if your king is in check after the move is made
//returns false if the move is illegal and true if it is legal
function testMove(newSquare, oldSquare, squares, castling, enpassent, turn) {

  //initialises test game states for the position after the move is made
  var newSquares
  var newCastling
  var newEnpassent
  //we want turn to be the same so we test if the right king is in check

  //makes a move and updates game states, same as what is done in the makeMove function
  if (isEnpassent(newSquare, oldSquare)) {//for enpassent moves
    newSquares=squares.map((squareCheck) => {
      if (squareCheck.id === newSquare.id) { 
        //moves the piece to the new square
        return {
          id:squareCheck.id,
          squareColor:squareCheck.squareColor,
          piece: oldSquare.piece,
          pieceColor: oldSquare.pieceColor,
          icon: oldSquare.icon,
        }
      } else if  (squareCheck.id === oldSquare.id) {
        //resets the square the piece is moving from
        return {
          id:squareCheck.id,
          squareColor:squareCheck.squareColor,
          piece: 0,
          pieceColor: '',
          icon: '',
        }
      } else if (squareCheck.id === enpassent) {
        //deletes the pawn on enpassent square
        return {
          id:squareCheck.id,
          squareColor:squareCheck.squareColor,
          piece: 0,
          pieceColor: '',
          icon: '',
        }
      } else {
        return {
          id:squareCheck.id,
          squareColor:squareCheck.squareColor,
          piece: squareCheck.piece,
          pieceColor: squareCheck.pieceColor,
          icon: squareCheck.icon,
        }
      }
    })
    newCastling= [castling[0], castling[1], castling[2], castling[3]]
    newEnpassent=0
  } else if(isCastle(newSquare, oldSquare)) { //for castling

    var num=oldSquare.id
    var oldId = 0
    var newId = 0
    if(oldSquare.pieceColor && num+2 === newSquare.id) { //white castle short
      newId=62
      oldId=64
    } else if(oldSquare.pieceColor && num-2 === newSquare.id) {  //white castle long
      newId=60
      oldId=57
    } else if(!oldSquare.pieceColor && num+2 === newSquare.id) { //black castle short
      newId=6
      oldId=8
    } else { //black castle long
      newId=4
      oldId=1
    }
    var newRook = {
      id:newId
    }
    var oldRook = {
      id:oldId,
      squareColor:getSquare(oldId, squares).squareColor,
      piece: getSquare(oldId, squares).piece,
      pieceColor: getSquare(oldId, squares).pieceColor,
      icon: getSquare(oldId, squares).icon,
    }

    newCastling=oldSquare.pieceColor ? [false, false, castling[2], castling[3]] : [castling[0], castling[1], false, false]
    newEnpassent=0
    newSquares = squares.map((squareCheck) => {
      if (squareCheck.id === newSquare.id) { 
        //moves the piece to the new square
        return {
          id:squareCheck.id,
          squareColor:squareCheck.squareColor,
          piece: oldSquare.piece,
          pieceColor: oldSquare.pieceColor,
          icon: oldSquare.icon,
        }
      } else if  (squareCheck.id === oldSquare.id) {
        //resets the square the piece is moving from
        return {
          id:squareCheck.id,
          squareColor:squareCheck.squareColor,
          piece: 0,
          pieceColor: '',
          icon: '',
        }
      } else if(squareCheck.id === oldRook.id) {
        return {
          id:squareCheck.id,
          squareColor:squareCheck.squareColor,
          piece: 0,
          pieceColor: '',
          icon: '',
        }
      } else if(squareCheck.id === newRook.id) {
        return {
          id:squareCheck.id,
          squareColor:squareCheck.squareColor,
          piece: oldRook.piece,
          pieceColor: oldRook.pieceColor,
          icon: oldRook.icon,
        }
      } else {
        return {
          id:squareCheck.id,
          squareColor:squareCheck.squareColor,
          piece: squareCheck.piece,
          pieceColor: squareCheck.pieceColor,
          icon: squareCheck.icon,
        }
      }
    })
  } else {//for normal moves
    newSquares=squares.map((squareCheck) => {
      if (squareCheck.id === newSquare.id) { 
        //moves the piece to the new square
        return {
          id:squareCheck.id,
          squareColor:squareCheck.squareColor,
          piece: oldSquare.piece,
          pieceColor: oldSquare.pieceColor,
          icon: oldSquare.icon,
        }
      } else if  (squareCheck.id === oldSquare.id) {
        //resets the square the piece is moving from
        return {
          id:squareCheck.id,
          squareColor:squareCheck.squareColor,
          piece: 0,
          pieceColor: '',
          icon: '',
        }
      } else {
        return {
          id:squareCheck.id,
          squareColor:squareCheck.squareColor,
          piece: squareCheck.piece,
          pieceColor: squareCheck.pieceColor,
          icon: squareCheck.icon,
        }
      }
    })
    newEnpassent=(Math.abs(newSquare.id-oldSquare.id)===16 && oldSquare.piece===1) ? newSquare.id : 0
    newCastling=changeCastle(oldSquare, newSquare, castling)
  }
  //Note: pormotion is not needed to be checked since if its in check and there is a pawn, same result for any other piece

  //checks if the user is in check in the new position
  //calls the safe version to prevent looping: testMove->inCheck->isAttacked->findMoves->pawnMove->testMove
  return !inCheckSafe(newSquares, turn, newCastling, newEnpassent)
}

//returns a board with a move actually made, no promotion though
function pretendMove(newSquare, oldSquare, squares, enpassent) {
  var newSquares

  //makes a move and updates board, same as what is done in the makeMove function
  if (isEnpassent(newSquare, oldSquare)) {//for enpassent moves
    newSquares=squares.map((squareCheck) => {
      if (squareCheck.id === newSquare.id) { 
        //moves the piece to the new square
        return {
          id:squareCheck.id,
          squareColor:squareCheck.squareColor,
          piece: oldSquare.piece,
          pieceColor: oldSquare.pieceColor,
          icon: oldSquare.icon,
        }
      } else if  (squareCheck.id === oldSquare.id) {
        //resets the square the piece is moving from
        return {
          id:squareCheck.id,
          squareColor:squareCheck.squareColor,
          piece: 0,
          pieceColor: '',
          icon: '',
        }
      } else if (squareCheck.id === enpassent) {
        //deletes the pawn on enpassent square
        return {
          id:squareCheck.id,
          squareColor:squareCheck.squareColor,
          piece: 0,
          pieceColor: '',
          icon: '',
        }
      } else {
        return {
          id:squareCheck.id,
          squareColor:squareCheck.squareColor,
          piece: squareCheck.piece,
          pieceColor: squareCheck.pieceColor,
          icon: squareCheck.icon,
        }
      }
    })
  } else if(isCastle(newSquare, oldSquare)) { //for castling

    var num=oldSquare.id
    var oldId = 0
    var newId = 0
    if(oldSquare.pieceColor && num+2 === newSquare.id) { //white castle short
      newId=62
      oldId=64
    } else if(oldSquare.pieceColor && num-2 === newSquare.id) {  //white castle long
      newId=60
      oldId=57
    } else if(!oldSquare.pieceColor && num+2 === newSquare.id) { //black castle short
      newId=6
      oldId=8
    } else { //black castle long
      newId=4
      oldId=1
    }
    var newRook = {
      id:newId
    }
    var oldRook = {
      id:oldId,
      squareColor:getSquare(oldId, squares).squareColor,
      piece: getSquare(oldId, squares).piece,
      pieceColor: getSquare(oldId, squares).pieceColor,
      icon: getSquare(oldId, squares).icon,
    }

    newSquares = squares.map((squareCheck) => {
      if (squareCheck.id === newSquare.id) { 
        //moves the piece to the new square
        return {
          id:squareCheck.id,
          squareColor:squareCheck.squareColor,
          piece: oldSquare.piece,
          pieceColor: oldSquare.pieceColor,
          icon: oldSquare.icon,
        }
      } else if  (squareCheck.id === oldSquare.id) {
        //resets the square the piece is moving from
        return {
          id:squareCheck.id,
          squareColor:squareCheck.squareColor,
          piece: 0,
          pieceColor: '',
          icon: '',
        }
      } else if(squareCheck.id === oldRook.id) {
        return {
          id:squareCheck.id,
          squareColor:squareCheck.squareColor,
          piece: 0,
          pieceColor: '',
          icon: '',
        }
      } else if(squareCheck.id === newRook.id) {
        return {
          id:squareCheck.id,
          squareColor:squareCheck.squareColor,
          piece: oldRook.piece,
          pieceColor: oldRook.pieceColor,
          icon: oldRook.icon,
        }
      } else {
        return {
          id:squareCheck.id,
          squareColor:squareCheck.squareColor,
          piece: squareCheck.piece,
          pieceColor: squareCheck.pieceColor,
          icon: squareCheck.icon,
        }
      }
    })
  } else {//for normal moves
    newSquares=squares.map((squareCheck) => {
      if (squareCheck.id === newSquare.id) { 
        //moves the piece to the new square
        return {
          id:squareCheck.id,
          squareColor:squareCheck.squareColor,
          piece: oldSquare.piece,
          pieceColor: oldSquare.pieceColor,
          icon: oldSquare.icon,
        }
      } else if  (squareCheck.id === oldSquare.id) {
        //resets the square the piece is moving from
        return {
          id:squareCheck.id,
          squareColor:squareCheck.squareColor,
          piece: 0,
          pieceColor: '',
          icon: '',
        }
      } else {
        return {
          id:squareCheck.id,
          squareColor:squareCheck.squareColor,
          piece: squareCheck.piece,
          pieceColor: squareCheck.pieceColor,
          icon: squareCheck.icon,
        }
      }
    })
  }

  return newSquares
}

//returns a board with the promotion move actually made
function pretendPromotion(newSquare, oldSquare, squares, enpassent, proPiece) {
  var newSquares

  //makes a move and updates board, same as what is done in the makeMove function
  if(oldSquare.pieceColor){//white
    switch (proPiece) {
      case 2: //bishop
        newSquares= squares.map((squareCheck) => {
          if (squareCheck.id === newSquare.id) { //moves the piece to the new square
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 2,
              pieceColor: oldSquare.pieceColor,
              icon: <img src={wbishop} className="piece-img" alt="wbishop"/>,
            }
          } else if  (squareCheck.id === oldSquare.id) {//resets the square the piece is moving from
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          } else { //stays the same if the square is unaffected by the move
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: squareCheck.piece,
              pieceColor: squareCheck.pieceColor,
              icon: squareCheck.icon,
            }
          }
        })
        break;
      case 3: //knight
        newSquares= squares.map((squareCheck) => {
          if (squareCheck.id === newSquare.id) { //moves the piece to the new square
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 3,
              pieceColor: oldSquare.pieceColor,
              icon: <img src={wknight} className="piece-img" alt="wknight"/>,
            }
          } else if  (squareCheck.id === oldSquare.id) {//resets the square the piece is moving from
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          } else { //stays the same if the square is unaffected by the move
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: squareCheck.piece,
              pieceColor: squareCheck.pieceColor,
              icon: squareCheck.icon,
            }
          }
        })
        break;
      case 4: //rook
        newSquares= squares.map((squareCheck) => {
          if (squareCheck.id === newSquare.id) { //moves the piece to the new square
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 4,
              pieceColor: oldSquare.pieceColor,
              icon: <img src={wrook} className="piece-img" alt="wrook"/>,
            }
          } else if  (squareCheck.id === oldSquare.id) {//resets the square the piece is moving from
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          } else { //stays the same if the square is unaffected by the move
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: squareCheck.piece,
              pieceColor: squareCheck.pieceColor,
              icon: squareCheck.icon,
            }
          }
        })
        break;
      case 5: //queen
        newSquares= squares.map((squareCheck) => {
          if (squareCheck.id === newSquare.id) { //moves the piece to the new square
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 5,
              pieceColor: oldSquare.pieceColor,
              icon: <img src={wqueen} className="piece-img" alt="wqueen"/>,
            }
          } else if  (squareCheck.id === oldSquare.id) {//resets the square the piece is moving from
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          } else { //stays the same if the square is unaffected by the move
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: squareCheck.piece,
              pieceColor: squareCheck.pieceColor,
              icon: squareCheck.icon,
            }
          }
        })
        break;
    }
  } else {//black
    switch (proPiece) {
      case 2: //bishop
        newSquares= squares.map((squareCheck) => {
          if (squareCheck.id === newSquare.id) { //moves the piece to the new square
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 2,
              pieceColor: oldSquare.pieceColor,
              icon: <img src={bbishop} className="piece-img" alt="bbishop"/>,
            }
          } else if  (squareCheck.id === oldSquare.id) {//resets the square the piece is moving from
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          } else { //stays the same if the square is unaffected by the move
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: squareCheck.piece,
              pieceColor: squareCheck.pieceColor,
              icon: squareCheck.icon,
            }
          }
        })
        break;
      case 3: //knight
        newSquares= squares.map((squareCheck) => {
          if (squareCheck.id === newSquare.id) { //moves the piece to the new square
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 3,
              pieceColor: oldSquare.pieceColor,
              icon: <img src={bknight} className="piece-img" alt="bknight"/>,
            }
          } else if  (squareCheck.id === oldSquare.id) {//resets the square the piece is moving from
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          } else { //stays the same if the square is unaffected by the move
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: squareCheck.piece,
              pieceColor: squareCheck.pieceColor,
              icon: squareCheck.icon,
            }
          }
        })
        break;
      case 4: //rook
        newSquares= squares.map((squareCheck) => {
          if (squareCheck.id === newSquare.id) { //moves the piece to the new square
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 4,
              pieceColor: oldSquare.pieceColor,
              icon: <img src={brook} className="piece-img" alt="brook"/>,
            }
          } else if  (squareCheck.id === oldSquare.id) {//resets the square the piece is moving from
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          } else { //stays the same if the square is unaffected by the move
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: squareCheck.piece,
              pieceColor: squareCheck.pieceColor,
              icon: squareCheck.icon,
            }
          }
        })
        break;
      case 5: //queen
        newSquares= squares.map((squareCheck) => {
          if (squareCheck.id === newSquare.id) { //moves the piece to the new square
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 5,
              pieceColor: oldSquare.pieceColor,
              icon: <img src={bqueen} className="piece-img" alt="bqueen"/>,
            }
          } else if  (squareCheck.id === oldSquare.id) {//resets the square the piece is moving from
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: 0,
              pieceColor: '',
              icon: '',
            }
          } else { //stays the same if the square is unaffected by the move
            return {
              id:squareCheck.id,
              squareColor:squareCheck.squareColor,
              piece: squareCheck.piece,
              pieceColor: squareCheck.pieceColor,
              icon: squareCheck.icon,
            }
          }
        })
        break;
    }
  }

  return newSquares
}

//returns an array of ids which the selected piece can move to
function findMoves(square, squares, castling, enpassent) {
  var moves=[]

  switch(square.piece) {
    case 1: //pawn
      moves=pawnMove(square, squares, castling, enpassent)
      break;
    case 2: //bishop
      moves=bishopMove(square, squares, castling, enpassent)
      break;
    case 3: //knight
      moves=knightMove(square, squares, castling, enpassent)
      break;
    case 4: //rook
      moves=rookMove(square, squares, castling, enpassent)
      break;
    case 5: //queen
      let movesD=bishopMove(square, squares, castling, enpassent)
      let movesS=rookMove(square, squares, castling, enpassent)
      moves=movesD.concat(movesS)
      break;
    case 6: //king
      moves=kingMove(square, squares, castling, enpassent)
      break;
  }

  return moves
}

//returns a square found by searching the ids
function getSquare(id, squares) {
  for (const square of squares) {
    if (square.id === id) {
      return square
    }
  }
}

//returns an array of ids a king can move from a certain square
function kingMove(square, squares, castling, enpassent) {
  var moves=[]
  var num=square.id

  //adds all standard moves to the list
  if((num-1) %8 === 0) {//when infinity wraps on the left side
    var newNum=num+1
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+7
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+8
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-8
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+15
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-7
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+9
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-1
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
  } else if ((num-1) %8 === 7) {//when infinity wraps on the right side
    var newNum=num-7
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-1
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+8
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-8
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+7
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-15
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+1
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-9
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
  } else {//when no wrapping is occuring
    var newNum=num+1
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-1
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+8
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-8
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+7
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-7
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+9
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-9
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
  }

  //determines if castling is possible
  //checks if the piece color is correct, that castling that way is allowed, that it will not pass through check, that it will not pass through other pieces, that it is not currently in check
  if(square.pieceColor && castling[0] && !isAttackedSafe(getSquare(59, squares), squares, castling, enpassent, true) && !isAttackedSafe(getSquare(60, squares), squares, castling, enpassent, true) && getSquare(60, squares).piece===0 && getSquare(59, squares).piece===0 && getSquare(58, squares).piece===0 && !inCheckSafe(squares, true, castling, enpassent)) {//white long
    moves.push(59)
  }
  if(square.pieceColor && castling[1] && !isAttackedSafe(getSquare(62, squares), squares, castling, enpassent, true) && !isAttackedSafe(getSquare(63, squares), squares, castling, enpassent, true) && getSquare(62, squares).piece===0 && getSquare(63, squares).piece===0 && !inCheckSafe(squares, true, castling, enpassent)) {//white short
    moves.push(63)
  }
  if(!square.pieceColor && castling[2] && !isAttackedSafe(getSquare(3, squares), squares, castling, enpassent, false) && !isAttackedSafe(getSquare(4, squares), squares, castling, enpassent, false) && getSquare(2, squares).piece===0 && getSquare(3, squares).piece===0 && getSquare(4, squares).piece===0 && !inCheckSafe(squares, false, castling, enpassent)) {//black long
    moves.push(3)
  }
  if(!square.pieceColor && castling[3] && !isAttackedSafe(getSquare(6, squares), squares, castling, enpassent, false) && !isAttackedSafe(getSquare(7, squares), squares, castling, enpassent, false) && getSquare(7, squares).piece===0 && getSquare(6, squares).piece===0 && !inCheckSafe(squares, false, castling, enpassent)) {//black short
    moves.push(7)
  }

  //removes all moves where you end up in check
  moves = moves.filter(move => testMove(getSquare(move, squares), square, squares, castling, enpassent, square.pieceColor))

  return moves
}

//returns an array of ids a rook can move from a certain square
function rookMove(square, squares, castling, enpassent) {
  var moves = []
  var num=square.id

  //loops through all squares protruding out from 'sqaure' in the 4 cardinal diractions until it reaches it's self again, reaches a piece, or reaches the edge of the board
  var newNum = num+8
  //checks the the new square is in the right range (1,64), that the new square is not on the same team, that the square last checked wasnt a square where the rook takes, that the horizontal moves dont loop
  while (newNum >= 1 && newNum <= 64 && getSquare(newNum, squares).pieceColor !== square.pieceColor && getSquare(newNum-8, squares).pieceColor !== !square.pieceColor) {
    moves.push(newNum)
    newNum+=8
  }
  //resets the square being checked
  newNum=num-8
  while (newNum >= 1 && newNum <= 64 && getSquare(newNum, squares).pieceColor !== square.pieceColor && getSquare(newNum+8, squares).pieceColor !== !square.pieceColor) {
    moves.push(newNum)
    newNum-=8
  }
  //resets the square being checked
  newNum=infinityRight(num+1)
  while (newNum >= 1 && newNum <= 64 && getSquare(newNum, squares).pieceColor !== square.pieceColor && getSquare(infinityLeft(newNum-1), squares).pieceColor !== !square.pieceColor) {
    moves.push(newNum)
    newNum=infinityRight(newNum+1)
  }
  //resets the square being checked
  newNum=infinityLeft(num-1)
  while (newNum >= 1 && newNum <= 64 && getSquare(newNum, squares).pieceColor !== square.pieceColor && getSquare(infinityRight(newNum+1), squares).pieceColor !== !square.pieceColor && square.id !== newNum) {
    moves.push(newNum)
    newNum=infinityLeft(newNum-1)
  }

  //removes all moves where you end up in check
  moves = moves.filter(move => testMove(getSquare(move, squares), square, squares, castling, enpassent, square.pieceColor))
  return moves
}

//returns an array of ids a knight can move from a certain square
function knightMove(square,squares, castling, enpassent) {
  var moves = []
  var num=square.id

  //checks all 8 squares a knight could move to end checks the the square is on the board and that the square doesnt have a piece from the same team on it
  if ((num-1) %8 === 0) { //for when it will wrap across the left side 4 times
    let newNum=num+14
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+10
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+23
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+17
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-6
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-2
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-15
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-9
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
  } else if ((num-1) %8 === 1) { //for when it will wrap across the left side 2 times
    let newNum=num+14
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+10
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+15
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+17
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-6
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-2
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-15
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-17
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
  } else if ((num-1) %8 === 7) { //for when it will wrap across the right side 4 times
    let newNum=num+6
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+2
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+15
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+9
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-14
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-10
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-23
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-17
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
  } else if ((num-1) %8 === 6) { //for when it will wrap across the right side 2 times
    let newNum=num+6
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+2
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+15
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+17
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-14
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-10
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-15
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-17
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
  } else { //for when it will not wrap
    let newNum=num+6
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+10
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+15
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+17
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-6
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-10
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-15
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-17
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
  }

  //removes all moves where you end up in check
  moves = moves.filter(move => testMove(getSquare(move, squares), square, squares, castling, enpassent, square.pieceColor))
  return moves
}

//returns an array of ids a bishop can move from a certain square
function bishopMove(square, squares, castling, enpassent) {
  var moves = []
  var num=square.id

  //loops through all squares protruding out from 'sqaure' in the 4 diagonal diractions until it reaches a piece, or reaches the edge of the board
  var newNum = infinityRight(num+9)
  //checks the the new square is in the right range (1,64), that the new square is not on the same team and that the square last checked wasnt a square where the rook takes
  while (newNum >= 1 && newNum <= 64 && getSquare(newNum, squares).pieceColor !== square.pieceColor && getSquare(infinityLeft(newNum-9), squares).pieceColor !== !square.pieceColor) {
    moves.push(newNum)
    newNum=infinityRight(newNum+9)
  }
  //resets the square being checked
  newNum=infinityLeft(num-9)
  while (newNum >= 1 && newNum <= 64 && getSquare(newNum, squares).pieceColor !== square.pieceColor && getSquare(infinityRight(newNum+9), squares).pieceColor !== !square.pieceColor) {
    moves.push(newNum)
    newNum=infinityLeft(newNum-9)
  }
  //resets the square being checked
  newNum=infinityLeft(num+7)
  while (newNum >= 1 && newNum <= 64 && getSquare(newNum, squares).pieceColor !== square.pieceColor && getSquare(infinityRight(newNum-7), squares).pieceColor !== !square.pieceColor) {
    moves.push(newNum)
    newNum=infinityLeft(newNum+7)
  }
  //resets the square being checked
  newNum=infinityRight(num-7)
  while (newNum >= 1 && newNum <= 64 && getSquare(newNum, squares).pieceColor !== square.pieceColor && getSquare(infinityLeft(newNum+7), squares).pieceColor !== !square.pieceColor) {
    moves.push(newNum)
    newNum=infinityRight(newNum-7)
  }

  //removes all moves where you end up in check
  moves = moves.filter(move => testMove(getSquare(move, squares), square, squares, castling, enpassent, square.pieceColor))
  return moves
}

//returns an array of ids a pawn can move from a certain square
function pawnMove(square, squares, castling, enpassent) {
  var moves = []
  var num=square.id
  var row=Math.ceil(square.id/8)

  if (square.pieceColor) { //white pawn
    //checks if the pawn can be pushed one square forawrd
    if(getSquare(num-8, squares).piece===0) {
     moves.push(num-8)
    }
    //checks if the pawn can be pushed forward 2 sqaures
    if(row===7 && getSquare(num-16, squares).piece===0)  {
      moves.push(num-16)
    }
    //checks if the pawn can take a piece diagonally left of it
    if(getSquare(infinityLeft(num-9), squares).pieceColor === !square.pieceColor) {
      moves.push(infinityLeft(num-9))
    }
    //checks if the pawn can take a piece diagonally right of it
    if(getSquare(infinityRight(num-7), squares).pieceColor === !square.pieceColor) {
      moves.push(infinityRight(num-7))
    }
    //checks if the pawn can take a piece enpassent diagonally right of it
    if (infinityRight(num+1) ===enpassent) {
      moves.push(infinityRight(num-7))
    }
    //checks if the pawn can take a piece enpassent diagonally left of it
    if (infinityLeft(num-1) ===enpassent) {
      moves.push(infinityLeft(num-9))
    }

  } else { //black pawn
    //checks if the pawn can be pushed one square forawrd
    if(getSquare(num+8, squares).piece===0) {
      moves.push(num+8)
    }
    //checks if the pawn can be pushed forward 2 sqaures
    if(row===2 && getSquare(num+16, squares).piece===0)  {
       moves.push(num+16)
    }
    //checks if the pawn can take a piece diagonally right of it
    if(getSquare(infinityRight(num+9), squares).pieceColor === !square.pieceColor) {
      moves.push(infinityRight(num+9))
    }
    //checks if the pawn can take a piece diagonally left of it
    if(getSquare(infinityLeft(num+7), squares).pieceColor === !square.pieceColor) {
      moves.push(infinityLeft(num+7))
    }
    //checks if the pawn can take a piece enpassent diagonally right of it
    if (infinityRight(num+1) ===enpassent) {
      moves.push(infinityRight(num+9))
    }
    //checks if the pawn can take a piece enpassent diagonally left of it
    if (infinityLeft(num-1) ===enpassent) {
      moves.push(infinityLeft(num+7))
    }
  }

  //removes all moves where you end up in check
  moves = moves.filter(move => testMove(getSquare(move, squares), square, squares, castling, enpassent, square.pieceColor))
  return moves
}

//determines if a player has no more moves in a position
function isOver(squares, turn, castling, enpassent) {
  var moves =[]

  //finds all possible moves by one team
  for (const square of squares) {
    if (square.pieceColor === turn) {
      moves = moves.concat(findMoves(square, squares, castling, enpassent))
    }
  }
  return moves.length === 0
}

//determines if a player is in check
function inCheck(squares, turn, castling, enpassent) {
  //looks through all the pieces of a player to find the king and determines if it is attacked
  for (const square of squares) {
    if (square.piece === 6 && square.pieceColor === turn) {
      return isAttacked(square, squares, castling, enpassent, turn)
    }
  }
}

//determiens if a certain square is attacked by not '!turn'
function isAttacked(square, squares, castling, enpassent, turn) {
  var color = turn
  var oppColor= !turn

  // loops through all squares on the board
  for (const squareCheck of squares) {
    //checks if the current squares has a piece on the opposite team
    if (squareCheck.pieceColor === oppColor) { 
      //checks if the piece will attack 'square'
      if (findMoves(squareCheck, squares, castling, enpassent).includes(square.id)) { 
        return true
      }
    }
  }

  return false
}

//fixes the id of a square when it calculated by a piece moving over the right side of the board
function infinityRight(id) {
  if (id%8===1) {
    return id-8
  }
  else {
    return id
  }
}

//fixes the id of a square when it calculated by a piece moving over the left side of the board
function infinityLeft(id) {
  if (id%8===0) {
    return id+8
  }
  else {
    return id
  }
}

/*  -----Safe versions of functions-----
Exact same as other version but wont lead to infinite looping.
No checking castling or if a move is impossible due to being in check next ply */


function inCheckSafe(squares, turn, castling, enpassent) {
  for (const square of squares) {
    if (square.piece === 6 && square.pieceColor === turn) {
      return isAttackedSafe(square, squares, castling, enpassent, turn)
    }
  }
}

function isAttackedSafe(square, squares, castling, enpassent, turn) {
  var color = turn
  var oppColor= !turn

  for (const squareCheck of squares) { // loops through all squares on the board
    if (squareCheck.pieceColor === oppColor) { //checks if the current squares has a piece on the opposite team
      if (findMovesSafe(squareCheck, squares, castling, enpassent).includes(square.id)) { //checks if the piece will attack square
        return true
      }
    }
  }

  return false
}

function findMovesSafe(square, squares, castling, enpassent) {
  var moves=[]

  switch(square.piece) {
    case 1: //pawn
      moves=pawnMoveSafe(square, squares, castling, enpassent)
      break;
    case 2: //bishop
      moves=bishopMoveSafe(square, squares, castling, enpassent)
      break;
    case 3: //knight
      moves=knightMoveSafe(square, squares, castling, enpassent)
      break;
    case 4: //rook
      moves=rookMoveSafe(square, squares, castling, enpassent)
      break;
    case 5: //queen
      let movesD=bishopMoveSafe(square, squares, castling, enpassent)
      let movesS=rookMoveSafe(square, squares, castling, enpassent)
      moves=movesD.concat(movesS)
      break;
    case 6: //king
      moves=kingMoveSafe(square, squares, castling, enpassent)
      break;
  }

  return moves
}

function kingMoveSafe(square, squares, castling, enpassent) {
  var moves=[]
  var num=square.id
  if((num-1) %8 === 0) {//when wraps on the left side
    var newNum=num+1
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+7
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+8
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-8
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+15
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-7
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+9
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-1
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
  } else if ((num-1) %8 === 7) {//when wraps on the right side
    var newNum=num-7
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-1
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+8
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-8
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+7
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-15
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+1
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-9
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
  } else {
    var newNum=num+1
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-1
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+8
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-8
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+7
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-7
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+9
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-9
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
  }


  //you dont need to check if king is safe because if king were to castle through a check were the taking of the king would result in a check against the other team, it wouldnt matter if you could giver a check because your king is gone
  return moves
}

function pawnMoveSafe(square, squares, castling, enpassent) {
  var moves = []
  var num=square.id
  var row=Math.ceil(square.id/8)

  if (square.pieceColor) { //white pawn
    if(getSquare(num-8, squares).piece===0) {
     moves.push(num-8)
    }
    if(row===7 && getSquare(num-16, squares).piece===0)  {
      moves.push(num-16)
    }
    if(getSquare(infinityLeft(num-9), squares).pieceColor === !square.pieceColor) {
      moves.push(infinityLeft(num-9))
    }
    if(getSquare(infinityRight(num-7), squares).pieceColor === !square.pieceColor) {
      moves.push(infinityRight(num-7))
    }
    if (infinityRight(num+1) ===enpassent) {
      moves.push(infinityRight(num-7))
    }
    if (infinityLeft(num-1) ===enpassent) {
      moves.push(infinityLeft(num-9))
    }
  } else { //black pawn
    if(getSquare(num+8, squares).piece===0) {
      moves.push(num+8)
     }
     if(row===2 && getSquare(num+16, squares).piece===0)  {
       moves.push(num+16)
     }
    if(getSquare(infinityRight(num+9), squares).pieceColor === !square.pieceColor) {
      moves.push(infinityRight(num+9))
    }
    if(getSquare(infinityLeft(num+7), squares).pieceColor === !square.pieceColor) {
      moves.push(infinityLeft(num+7))
    }
    if (infinityRight(num+1) ===enpassent) {
      moves.push(infinityRight(num+9))
    }
    if (infinityLeft(num-1) ===enpassent) {
      moves.push(infinityLeft(num+7))
    }
  }

  return moves
}

function rookMoveSafe(square, squares, castling, enpassent) {
  var moves = []
  var num=square.id

  var newNum = num+8
  //checks the the new square is in the right range (1,64), that the new square is not on the same team, that the square last checked wasnt a square where the rook takes, that the horizontal moves dont loop
  while (newNum >= 1 && newNum <= 64 && getSquare(newNum, squares).pieceColor !== square.pieceColor && getSquare(newNum-8, squares).pieceColor !== !square.pieceColor) {
    moves.push(newNum)
    newNum+=8
  }
  newNum=num-8
  while (newNum >= 1 && newNum <= 64 && getSquare(newNum, squares).pieceColor !== square.pieceColor && getSquare(newNum+8, squares).pieceColor !== !square.pieceColor) {
    moves.push(newNum)
    newNum-=8
  }
  newNum=infinityRight(num+1)
  while (newNum >= 1 && newNum <= 64 && getSquare(newNum, squares).pieceColor !== square.pieceColor && getSquare(infinityLeft(newNum-1), squares).pieceColor !== !square.pieceColor) {
    moves.push(newNum)
    newNum=infinityRight(newNum+1)
  }
  newNum=infinityLeft(num-1)
  while (newNum >= 1 && newNum <= 64 && getSquare(newNum, squares).pieceColor !== square.pieceColor && getSquare(infinityRight(newNum+1), squares).pieceColor !== !square.pieceColor && square.id !== newNum) {
    moves.push(newNum)
    newNum=infinityLeft(newNum-1)
  }

  return moves
}

function knightMoveSafe(square,squares, castling, enpassent) {
  var moves = []
  var num=square.id

  if ((num-1) %8 === 0) { //for when it will wrap across the left side
    let newNum=num+14
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+10
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+23
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+17
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-6
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-2
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-15
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-9
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
  } else if ((num-1) %8 === 1) { //for when it will wrap across the left side
    let newNum=num+14
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+10
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+15
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+17
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-6
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-2
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-15
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-17
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
  } else if ((num-1) %8 === 7) { //for when it will wrap across the right side
    let newNum=num+6
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+2
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+15
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+9
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-14
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-10
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-23
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-17
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
  } else if ((num-1) %8 === 6) { //for when it will wrap across the right side
    let newNum=num+6
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+2
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+15
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+17
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-14
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-10
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-15
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-17
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
  } else { //for when it will not wrap
    let newNum=num+6
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+10
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+15
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num+17
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-6
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-10
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-15
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
    newNum=num-17
    if(newNum>=1 && newNum<=64 && getSquare(newNum, squares).pieceColor !== square.pieceColor){
      moves.push(newNum)
    }
  }

  return moves
}

function bishopMoveSafe(square, squares, castling, enpassent) {
  var moves = []
  var num=square.id

  var newNum = infinityRight(num+9)
  //checks the the new square is in the right range (1,64), that the new square is not on the same team and that the square last checked wasnt a square where the rook takes
  while (newNum >= 1 && newNum <= 64 && getSquare(newNum, squares).pieceColor !== square.pieceColor && getSquare(infinityLeft(newNum-9), squares).pieceColor !== !square.pieceColor) {
    moves.push(newNum)
    newNum=infinityRight(newNum+9)
  }
  newNum=infinityLeft(num-9)
  while (newNum >= 1 && newNum <= 64 && getSquare(newNum, squares).pieceColor !== square.pieceColor && getSquare(infinityRight(newNum+9), squares).pieceColor !== !square.pieceColor) {
    moves.push(newNum)
    newNum=infinityLeft(newNum-9)
  }
  newNum=infinityLeft(num+7)
  while (newNum >= 1 && newNum <= 64 && getSquare(newNum, squares).pieceColor !== square.pieceColor && getSquare(infinityRight(newNum-7), squares).pieceColor !== !square.pieceColor) {
    moves.push(newNum)
    newNum=infinityLeft(newNum+7)
  }
  newNum=infinityRight(num-7)
  while (newNum >= 1 && newNum <= 64 && getSquare(newNum, squares).pieceColor !== square.pieceColor && getSquare(infinityLeft(newNum+7), squares).pieceColor !== !square.pieceColor) {
    moves.push(newNum)
    newNum=infinityRight(newNum-7)
  }

  return moves
}

export default Game_engine;
