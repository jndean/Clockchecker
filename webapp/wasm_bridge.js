import createClockcheckerModule from './clockchecker_wasm.js';

let _mod = null;
let _puzzleSize = 0;
let _solutionSize = 0;

export async function initWasm() {
    if (_mod) return _mod;
    _mod = await createClockcheckerModule();
    _puzzleSize = _mod._get_serialized_puzzle_size();
    _solutionSize = _mod._get_serialized_solution_size();
    return _mod;
}

export function getPuzzleSize() {
    return _puzzleSize;
}

export function getSolutionSize() {
    return _solutionSize;
}

export function solveStream(puzzleBytes, onSolution) {
    if (!_mod) {
        throw new Error('WASM module not initialized. Call initWasm() first.');
    }
    const bytes = puzzleBytes instanceof Uint8Array ? puzzleBytes : new Uint8Array(puzzleBytes);
    if (bytes.length !== _puzzleSize) {
        throw new Error(`SerializedPuzzle size mismatch: JS=${bytes.length} vs WASM=${_puzzleSize}`);
    }
    const puzzlePtr = _mod._malloc(_puzzleSize);
    if (!puzzlePtr) {
        throw new Error('WASM _malloc failed for SerializedPuzzle');
    }
    const cbPtr = _mod.addFunction((solPtr, _ctx) => {
        const solCopy = _mod.HEAPU8.slice(solPtr, solPtr + _solutionSize);
        return onSolution(solCopy) ? 1 : 0;
    }, 'ipp');

    try {
        _mod.HEAPU8.set(bytes, puzzlePtr);
        return _mod._solve_puzzle_cpp_stream(puzzlePtr, 1, cbPtr, 0);
    } finally {
        _mod.removeFunction(cbPtr);
        _mod._free(puzzlePtr);
    }
}

