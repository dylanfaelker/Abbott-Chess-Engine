# V2.2
- Adjusted centipawn values of Mobility, Control, and King Safety
    - Mobility now worth 5
    - Control of opponents side worth 10
    - Extra attacker around king worth 20
- Iterative deepening (https://www.chessprogramming.org/Iterative_Deepening)
- Move ordering (https://www.chessprogramming.org/Move_Ordering)
    - Hash move (https://www.chessprogramming.org/Hash_Move)
    - MVV-LVA hueristic (https://www.chessprogramming.org/MVV-LVA)
    - Killer hueristic (https://www.chessprogramming.org/Killer_Heuristic)
    - Promotions
- Transposition table (https://www.chessprogramming.org/Transposition_Table)
    - For previously evaluated positions and move ordering
- Quiescence search (https://www.chessprogramming.org/Quiescence_Search)
    - Looking at every capture
- Initiative evaluation
    - Who ever moves next gets 10 centipawns bonus
- Piece-Square Tables (https://www.chessprogramming.org/Piece-Square_Tables)
    - Custom tables for better adaptation to infinity chess rules
- Randomness for the sake of variation in play optional
    - Somewhere between ±5 centipawns added to each eval



# V2.1
- Moved to python flask server
- Similar logic as V1.1
- Negamax instead of minimax (https://www.chessprogramming.org/Negamax)


# V1.1
- Minimax (https://www.chessprogramming.org/Minimax)
- Alpha beta pruning (https://www.chessprogramming.org/Alpha-Beta)
- Material valuation (https://www.chessprogramming.org/Material)
    - Similar to standard understanding of pawn=1, knight=3, rook=5, queen=9
    - Bishop is given 400 due to increased movement in infinity chess
- Mobility (https://www.chessprogramming.org/Mobility) 
    - 10 centipawns are given for every legal move
- Control
    - Extra 10 centipawns are given for mobility to square on the opponents side
- King Safety (https://www.chessprogramming.org/King_Safety)
    - 25 centipawns are given for every extra attacker on a square next to the opposing king, compared to the number of defenders