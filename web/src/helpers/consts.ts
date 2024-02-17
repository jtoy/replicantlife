export enum DIRECTION {
    left,
    right,
    up,
    down
}

export const DIRECTION_UPDATE_MAP = {
    [DIRECTION.left]: {x: -1, y: 0},
    [DIRECTION.right]: {x: 1, y: 0},
    [DIRECTION.up]: {x: 0, y: -1},
    [DIRECTION.down]: {x: 0, y: 1}
}



export const CELL_SIZE = 32;