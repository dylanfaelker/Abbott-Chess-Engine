const Square = ({ square, onSelect, moves, selectedNum, lastMove, wcheck, bcheck }) => {
    return (
        <div 
            className={(square.id === wcheck || square.id === bcheck) ? 'square-check' : (moves.includes(square.id) ? 'square-highlight' : (selectedNum === square.id ? 'square-chosen' : (square.id === lastMove ? 'square-last' : (((square.id%8 + Math.floor((square.id-1) / 8))%2)  ? 'square-white' : "square-black"))))}
            onClick={() => onSelect(square)}
        >
            {square.icon}
        </div>
    )
}

export default Square
