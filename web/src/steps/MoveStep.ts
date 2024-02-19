import { DIRECTION } from "@/helpers/consts";
import Level from "../classes/Level";
import { Step, StepJSON } from "./Step";
import { GridPosition } from "@/classes/Agent";


export interface MoveJSON extends StepJSON {
    x: number;
    y: number;
    agent_id: string;
    agent_name: string;
}


export class MoveStep extends Step {
    direction: DIRECTION;
    agentId: string;
    newPosition: GridPosition;

    constructor(stepId: number, substepId: number, direction: DIRECTION, agentId: string, newPosition: GridPosition) {
        super(stepId, substepId);   
        this.direction = direction;
        this.agentId = agentId;
        this.newPosition = newPosition;
    }

    static fromJSON(json: MoveJSON): MoveStep {
        const { step, substep, agent_id, x, y } = json;
        return new MoveStep(step, substep, DIRECTION.right, agent_id, { x, y });
    }

    applyStep(level: Level) {
        const placement = level.findAgentPlacement(this.agentId);

        if (!placement) {
            return;
        }

        placement.position = this.newPosition;
    }
}
