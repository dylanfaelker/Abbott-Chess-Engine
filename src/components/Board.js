import Square from './Square'

const Board = ({ squares, onSelect, moves, selectedNum, }) => {

    return (
        <>
            <div className="board-row">
                {squares.slice(0,8).map((square) => (
                    <Square
                        key={square.id} 
                        square={square}
                        onSelect={onSelect} 
                        moves={moves}
                        selectedNum={selectedNum}
                    />
                ))} 
            </div>
            <div className="board-row">
                {squares.slice(8,16).map((square) => (
                    <Square
                        key={square.id} 
                        square={square} 
                        onSelect={onSelect} 
                        moves={moves}
                        selectedNum={selectedNum}
                    />
                ))} 
            </div>
            <div className="board-row">
                {squares.slice(16,24).map((square) => (
                    <Square
                        key={square.id} 
                        square={square} 
                        onSelect={onSelect} 
                        moves={moves}
                        selectedNum={selectedNum}
                    />
                ))} 
            </div>
            <div className="board-row">
                {squares.slice(24,32).map((square) => (
                    <Square
                        key={square.id} 
                        square={square} 
                        onSelect={onSelect} 
                        moves={moves}
                        selectedNum={selectedNum}
                    />
                ))} 
            </div>
            <div className="board-row">
                {squares.slice(32,40).map((square) => (
                    <Square
                        key={square.id} 
                        square={square} 
                        onSelect={onSelect} 
                        moves={moves}
                        selectedNum={selectedNum}
                    />
                ))} 
            </div>
            <div className="board-row">
                {squares.slice(40,48).map((square) => (
                    <Square
                        key={square.id} 
                        square={square} 
                        onSelect={onSelect} 
                        moves={moves}
                        selectedNum={selectedNum}
                    />
                ))} 
            </div>
            <div className="board-row">
                {squares.slice(48,56).map((square) => (
                    <Square
                        key={square.id} 
                        square={square} 
                        onSelect={onSelect} 
                        moves={moves}
                        selectedNum={selectedNum}
                    />
                ))} 
            </div>
            <div className="board-row">
                {squares.slice(56,64).map((square) => (
                    <Square
                        key={square.id} 
                        square={square} 
                        onSelect={onSelect} 
                        moves={moves}
                        selectedNum={selectedNum}
                    />
                ))} 
            </div>
        </>
    )
}

export default Board
