import Level from "@/classes/Level";
import { StepJSON, Step } from "./Step";

export interface MatrixSetJSON extends StepJSON {
    status: string;
}

export class MatrixSetStep extends Step {
    status: string;

    constructor(stepId: number, substepId: number, status: string) {
        super(stepId, substepId);
        this.status = status;
    }

    static fromJSON(json: MatrixSetJSON): MatrixSetStep {
        return new MatrixSetStep(json.step, json.substep, json.status);
    }
    
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    applyStep(level: Level) {
        level.simulationComplete = true;
    }
}