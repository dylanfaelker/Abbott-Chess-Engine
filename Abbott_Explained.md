# Abbott Chess Engine Explained

Abbott is a hand-crafted chess engine for **Infinity Chess**. It does not use machine learning or a neural network. Instead, it combines a classic game-tree **search** with a hand-written **evaluation function** to decide which move is best.[^hce]

The engine can be described in two layers:

1. [**Search**](#search)
2. [**Evaluation**](#evaluation)

## High-Level Idea

On each turn, Abbott:

1. Generates all **legal moves** for the side to move.[^legal]
2. Builds a **negamax** search tree to examine replies and counter-replies.[^negamax]
3. Uses **alpha-beta pruning** to skip branches that cannot affect the final choice.[^alphabeta]
4. Extends the search with **quiescence search** in tactical positions, mainly captures, to avoid unstable leaf evaluations.[^quiescence][^horizon]
5. Scores the resulting positions with a **static evaluation function** measured in **centipawns**.[^centipawn]
6. Returns the move with the best final score.

## Search

### 1. Negamax Framework [^negamax]

Abbott uses **negamax**, a standard way to write a two-player adversarial search.

The idea is simple:

- A good position for White is bad for Black.
- Because of that symmetry, the engine can use one scoring routine for both sides.
- After searching a child position, it flips the score's sign when returning to the parent node.

### 2. Alpha-Beta Pruning [^alphabeta]

Searching every possible continuation quickly becomes too expensive, so Abbott applies **alpha-beta pruning**.

- `alpha` is the best score already guaranteed for the side to move.
- `beta` is the opponent's cutoff threshold.
- If a branch becomes so good for one side that the opponent would never allow it, the rest of that branch is ignored.

This does not change the best move. It only makes the engine faster by avoiding useless work.

### 3. Iterative Deepening [^iterdeep]

Abbott searches depth `1`, then depth `2`, then depth `3`, and so on up to the requested limit. This is called **iterative deepening**.

This helps in two ways:

- The engine always has a usable best move from the last completed depth.
- Results from shallow searches can improve **move ordering** at deeper levels.[^moveordering]

While this might seem like a lot of extra work being done, it is actually sometimes faster than immediatly checking the max depth due to the saves with move ordering and alpha-beta pruning.

### 4. Move Ordering [^moveordering]

Alpha-beta pruning becomes much stronger when the best moves are searched first, so Abbott sorts moves using several heuristics. Each hueristic applies a score to a move with the higher priority hueristics having more weight. The moves are then searched in the order of their scores.

1. **Transposition-table move first**: if a previous search already found a strong move in the same position, search it first.[^tt][^hashmove]
    - Score: 100,000
2. **Captures** are sorted using **MVV-LVA** ("Most Valuable Victim, Least Valuable Attacker").[^mvvlva]
    - Score: 10,000 + 10 * VICTIM_VALUE - ATTACKER_VALUE
    - Range: [18,900, 10,100]
3. **Killer moves** are tried early if they previously caused a cutoff at the same search depth.[^killer]
    - Score: 9,000
4. **Promotions** are also pushed higher in the order.
    - Score: 8,000

Better move ordering means more cutoffs, and more cutoffs mean faster searchs.

### 5. Transposition Table [^tt]

Different move orders can lead to the same board position. Abbott stores previously searched results in a **transposition table** so it does not need to fully solve the same position again.

Each stored entry includes:

- the position hash,
- the depth searched,
- the score,
- the bound type (`exact`, `lower`, or `upper`),
- and the best move found from that position.

To identify positions efficiently, the board state is converted into a **Zobrist hash**.[^zobrist]

### 6. Quiescence Search [^quiescence]

Stopping search at a fixed depth can produce misleading evaluations if the final position is tactically unstable. Abbott handles that with **quiescence search**.

At the normal search limit, instead of evaluating immediately, the engine continues exploring forcing capture sequences until the position is quieter. This reduces the **horizon effect**, where the engine misses an important tactical event just beyond the nominal depth.[^horizon]

### 7. Checkmate and Draw Handling

The search also checks whether the game is already over:

- **Checkmate** returns a very large score.
- Faster mates are preferred over slower mates.
- **Draws** return a neutral score.

This lets Abbott treat mate as more important than ordinary material or positional advantages.

## Evaluation

Abbott's evaluator is a **hand-crafted evaluation** function.[^hce] It does not learn weights from data. Instead, the scoring rules are written explicitly in code.

The total evaluation is mainly built from four parts:

1. **Material**
2. **Board control**
3. **King Safety**
4. **Piece-square bonuses**

The final score is returned from **White's perspective**:

- positive score = White is better
- negative score = Black is better

### 1. Material [^material]

Material is the base of the evaluation.

Abbott uses these piece values: [^centipawn]

- Pawn = `100`
- Knight = `300`
- Bishop = `400`
- Rook = `500`
- Queen = `900`
- King = `100,000`

One notable Infinity Chess choice is that the **bishop is valued at 400 instead of 300**. Because of horizontal wrapping, bishops can become much more slippery and dangerous than in normal chess.

### 2. Board Control

Abbott builds an **attack map** for both sides using **pseudo-legal moves**.[^pseudo]

It then rewards square control:

- squares on your own half are worth less,
    - 5 centipawns
- squares on the opponent's half are worth more.
    - 10 centipawns

These are only counted for each individual square being attacked. There is no extra points for having a two pieces attacking the same square.

This encourages active play and forward pressure rather than passive piece placement.

### 3. King Safety [^kingsafety]

King safety is evaluated using the squares around each king.

For each square around the king:

- the engine compares enemy attackers to friendly defenders,
- if the enemy has more pressure, the position is penalized.
    - 20 centipawns for each extra attacker. 
- There is no bonus for overly defended squares.
    - The best score defensively is 0.

This means the engine is not only counting direct threats to the king itself. It is also measuring how weak the surrounding shelter has become.

### 4. Initiative

Abbott gives a small bonus to the side to move. This is a simple **initiative** term.
- This is worth 10 centipawns

The idea is that having the next move is usually worth something, especially in active or tactical positions.

### 5. Piece-Square Tables [^pst]

On standard `8x8` boards, Abbott also uses **piece-square tables**.
- The table values are implemented in [`engine/evaluate.py`](engine/evaluate.py#L95).

These are pre-written lookup tables that reward good placement for each piece type. For example:

- pawns are encouraged to advance sensibly,
- knights are rewarded for central activity,
- kings are guided toward safer squares.

Because Infinity Chess wraps horizontally, the tables are shifted so they stay aligned with the enemy king's file. A "center of the board" does not exist in Infinity Chess. It could be the `d` and `e` files, or it could be the `a` and `h` files, depending on how the game unfolds. The shift makes the positional bonuses more relevant to the wrapped board geometry.

### 6. Small Random Variation

The main engine can optionally add a very small random value to the evaluation. This creates a little variety so the engine does not always choose the exact same move in equal positions.
    - The random value ranges from -5 to 5 centipawns.


---

[^alphabeta]: [Alpha-Beta](https://www.chessprogramming.org/Alpha-Beta)
[^centipawn]: [Centipawns](https://www.chessprogramming.org/Centipawns)
[^classical]: [Classical Approach](https://www.chessprogramming.org/Classical_Approach)
[^hashmove]: [Hash Move](https://www.chessprogramming.org/Hash_Move)
[^hce]: [Evaluation](https://www.chessprogramming.org/Evaluation)
[^horizon]: [Horizon Effect](https://www.chessprogramming.org/Horizon_Effect)
[^iterdeep]: [Iterative Deepening](https://www.chessprogramming.org/Iterative_Deepening)
[^killer]: [Killer Heuristic](https://www.chessprogramming.org/Killer_Heuristic)
[^kingsafety]: [King Safety](https://www.chessprogramming.org/King_Safety)
[^legal]: [Legal Move](https://www.chessprogramming.org/Legal_Move)
[^material]: [Material](https://www.chessprogramming.org/Material)
[^moveordering]: [Move Ordering](https://www.chessprogramming.org/Move_Ordering)
[^mvvlva]: [MVV-LVA](https://www.chessprogramming.org/MVV-LVA)
[^negamax]: [Negamax](https://www.chessprogramming.org/Negamax)
[^pseudo]: [Pseudo-Legal Move](https://www.chessprogramming.org/Pseudo-Legal_Move)
[^pst]: [Piece-Square Tables](https://www.chessprogramming.org/Piece-Square_Tables)
[^quiescence]: [Quiescence Search](https://www.chessprogramming.org/Quiescence_Search)
[^tt]: [Transposition Table](https://www.chessprogramming.org/Transposition_Table)
[^zobrist]: [Zobrist Hashing](https://www.chessprogramming.org/Zobrist_Hashing)
