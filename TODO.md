# TODO:

-   [x] Select what to write the GUI in
    -   [x] Tkinter?
    -   [ ] Other UI?
-   [x] Chessboard display
    -   [ ] Allow setting up board state in some convenient way
    -   [x] Display variant pieces
        -   [ ] Support custom piece-sets
    -   [x] Allow inputting moves (in a way that supports even weird
        variants like amazons)
        -   [ ] By drag-and-drop
        -   [x] By clicking the from and to square
            -   [x] Display possible moves after selecting a piece
        -   [ ] By keyboard input
    -   [ ] Show players and timers
    -   [ ] Piece movement animations
    -   [ ] Keyboard shortcuts for moving through history, etc
-   [ ] Other displays
    -   [ ] Game history
        -   [ ] With analysis annotations
        -   [ ] In compact form (inline text, PGN-like)
        -   [ ] In table form (like lichess)
        -   [ ] Supporting variations
        -   [ ] And nested variations
    -   [ ] Engine output
        -   [ ] MultiPV
    -   [ ] Evaluation bar
-   [x] UCI Protocol
    -   [x] Connect to Fairy-Stockfish (or other engine)
    -   [x] Allow setting options
        -   [x] While running
    -   [ ] Set up positions
    -   [x] Search positions
        -   [x] With proper time control info
    -   [x] Return bestmove results in a convenient format
    -   [x] Stop calculating
-   [ ] Other
    -   [ ] Save/load FEN
    -   [ ] Import/export PGN
    -   [ ] Play engine vs engine tournaments
    -   [ ] Implement time controls, simple increment, N moves in T
        time, N seconds per move, ...
